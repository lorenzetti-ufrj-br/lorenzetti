import unittest
from GaugiKernel.Configurable import Configurable
from GaugiKernel.ComponentAccumulator import ComponentAccumulator


class MockAlgorithm:
    def __init__(self, name):
        self._name = name
        self._properties = []

    def name(self):
        return self._name

    def getProperties(self):
        return self._properties

    def hasProperty(self, name):
        return name in self._properties

    def setProperty(self, name, value):
        setattr(self, name, value)


class MockReaderAlgorithm(MockAlgorithm):
    def __init__(self, name):
        super().__init__(name)
        self._properties = ["InputFile", "OutputCellsKey", "OutputSeedsKey"]
        self.InputFile = "sample.root"
        self.OutputCellsKey = "Cells"
        self.OutputSeedsKey = "Seeds"


class MockClusterAlgorithm(MockAlgorithm):
    def __init__(self, name):
        super().__init__(name)
        self._properties = ["InputCellsKey", "InputSeedsKey", "OutputClusterKey"]
        self.InputCellsKey = "Cells"
        self.InputSeedsKey = "Seeds"
        self.OutputClusterKey = "Clusters"


class MockMakerAlgorithm(MockAlgorithm):
    def __init__(self, name):
        super().__init__(name)
        self._properties = ["ItemList", "TreeName"]
        self.ItemList = ["CaloClusterContainer#Clusters"]
        self.TreeName = "CollectionTree"


class TestComponentAccumulatorTree(unittest.TestCase):
    """Unit tests for ComponentAccumulator sequence tracking and StoreGate data flow tree."""

    def test_configurable_container_introspection(self):
        cluster_alg = Configurable(
            MockClusterAlgorithm,
            "ClusterMaker",
            InputCellsKey="Cells",
            InputSeedsKey="Seeds",
            OutputClusterKey="Clusters",
        )
        self.assertEqual(cluster_alg.name(), "ClusterMaker")
        self.assertEqual(cluster_alg.getTypeName(), "MockClusterAlgorithm")
        self.assertEqual(cluster_alg.getInputContainers(), ["Cells", "Seeds"])
        self.assertEqual(cluster_alg.getOutputContainers(), ["Clusters"])

        maker_alg = Configurable(
            MockMakerAlgorithm,
            "AODMaker",
            ItemList=["CaloClusterContainer#Clusters"],
        )
        self.assertEqual(maker_alg.getInputContainers(), ["Clusters"])

    def test_component_accumulator_sequence_and_tree(self):
        reader = Configurable(MockReaderAlgorithm, "MyReader")
        acc = ComponentAccumulator("TestAcc", "output.root", reader)

        alg1 = Configurable(
            MockClusterAlgorithm,
            "ClusterMaker",
            InputCellsKey="Cells",
            InputSeedsKey="Seeds",
            OutputClusterKey="Clusters",
        )
        alg2 = Configurable(
            MockMakerAlgorithm,
            "AODMaker",
            ItemList=["CaloClusterContainer#Clusters"],
        )

        acc += alg1
        acc += alg2

        seq = acc.get_sequence()
        self.assertEqual(len(seq), 2)
        self.assertEqual(seq[0].name(), "ClusterMaker")
        self.assertEqual(seq[1].name(), "AODMaker")

        tree_str = str(acc)
        self.assertIn("ComponentAccumulator: TestAcc", tree_str)
        self.assertIn("EXECUTION SEQUENCE", tree_str)
        self.assertIn("[Reader] MockReaderAlgorithm/MyReader", tree_str)
        self.assertIn("[0] MockClusterAlgorithm/ClusterMaker", tree_str)
        self.assertIn("[1] MockMakerAlgorithm/AODMaker", tree_str)
        self.assertIn("DATA FLOW & CONTAINER LINEAGE (StoreGate EDM Tree)", tree_str)
        self.assertIn("Cells", tree_str)
        self.assertIn("Clusters", tree_str)
        self.assertIn("Produced by: ClusterMaker", tree_str)
        self.assertIn("Consumed by: AODMaker", tree_str)


if __name__ == "__main__":
    unittest.main()

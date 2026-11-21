import unittest
import os
import tempfile
from pathlib import Path
import ROOT

from EgammaMonitoring import (
    EgammaMonitoringMakerCfg,
    EgammaMonitoringCfg,
    EgammaMonitoringMaker,
    EgammaMonitoring,
)


class TestMonitoring(unittest.TestCase):
    """Unit tests for EgammaMonitoringMaker configuration, StoreGate booking, and DQM utilities."""

    @classmethod
    def setUpClass(cls):
        ROOT.gROOT.SetBatch(True)
        ROOT.gSystem.Load("liblorenzetti")

    def test_monitoring_cfg_instantiation(self):
        alg = EgammaMonitoringMakerCfg(
            "TestEgammaMonitoring",
            Directory="Expert-Test",
            InputEventInfoKey="TestEvents",
            InputClusterKey="TestClusters",
            InputElectronKey="TestElectrons",
            InputRingsKey="TestRings",
        )
        self.assertEqual(alg.name(), "TestEgammaMonitoring")
        self.assertEqual(alg.Directory, "Expert-Test")
        self.assertEqual(alg.InputEventInfoKey, "TestEvents")
        self.assertEqual(alg.InputClusterKey, "TestClusters")
        self.assertEqual(alg.InputElectronKey, "TestElectrons")
        self.assertEqual(alg.InputRingsKey, "TestRings")
        self.assertEqual(alg.InputRingsKeys, ["TestRings"])

    def test_monitoring_all_rings_keys(self):
        alg = EgammaMonitoringMakerCfg("AllRingsMon")
        self.assertEqual(len(alg.InputRingsKeys), 6)
        self.assertIn("Rings", alg.InputRingsKeys)
        self.assertIn("Rings_Asym", alg.InputRingsKeys)
        self.assertIn("Rings_Cross", alg.InputRingsKeys)
        self.assertIn("Rings_Corner", alg.InputRingsKeys)
        self.assertIn("Rings_Strips", alg.InputRingsKeys)
        self.assertIn("Rings_Custom", alg.InputRingsKeys)

    def test_aliases(self):
        alg1 = EgammaMonitoringCfg("Alias1")
        alg2 = EgammaMonitoringMaker("Alias2")
        alg3 = EgammaMonitoring("Alias3")
        self.assertEqual(alg1.name(), "Alias1")
        self.assertEqual(alg2.name(), "Alias2")
        self.assertEqual(alg3.name(), "Alias3")

    def test_cpp_class_instantiation(self):
        alg_cls = getattr(ROOT, "EgammaMonitoringMaker", getattr(ROOT.Gaugi, "EgammaMonitoringMaker", None))
        self.assertIsNotNone(alg_cls)
        instance = alg_cls("CppEgammaMonitoring")
        self.assertEqual(instance.name(), "CppEgammaMonitoring")
        self.assertEqual(instance.directory(), "Expert-Monitoring")

    def test_storegate_booking_and_retrieval(self):
        """Verifies bookHistograms registers all directories and histograms into StoreGate."""
        from ROOT import SG
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_storegate_mon.root")
            store = SG.StoreGate(test_file)
            ctx = SG.EventContext("EventContext")
            ctx.setStoreGateSvc(store)

            alg_cls = getattr(ROOT, "EgammaMonitoringMaker", getattr(ROOT.Gaugi, "EgammaMonitoringMaker", None))
            mon = alg_cls("TestMonStoreGate")
            self.assertTrue(mon.initialize().isSuccess())
            self.assertTrue(mon.bookHistograms(ctx).isSuccess())

            # Check EventInfo
            store.cd("Expert-Monitoring/EventInfo")
            h_avgmu = store.hist1("avgmu")
            self.assertIsNotNone(h_avgmu)
            self.assertEqual(h_avgmu.GetName(), "avgmu")

            # Check Kinematics
            store.cd("Expert-Monitoring/Kinematics")
            h_clet = store.hist1("cl_et")
            self.assertIsNotNone(h_clet)

            # Check ShowerShapes
            store.cd("Expert-Monitoring/ShowerShapes")
            h_reta = store.hist1("reta")
            self.assertIsNotNone(h_reta)

            # Check Moments
            store.cd("Expert-Monitoring/Moments")
            h_mom = store.hist1("secondLambda")
            self.assertIsNotNone(h_mom)

            # Check PID
            store.cd("Expert-Monitoring/PID")
            h_pid = store.hist1("electron_pid_pass")
            self.assertIsNotNone(h_pid)
            self.assertEqual(h_pid.GetXaxis().GetBinLabel(1), "VeryLoose")
            self.assertEqual(h_pid.GetXaxis().GetBinLabel(4), "Tight")

            # Check Rings (all 6 topologies)
            store.cd("Expert-Monitoring/Rings")
            self.assertIsNotNone(store.hist1("rings_profile"))
            self.assertIsNotNone(store.hist1("rings_asym_profile"))
            self.assertIsNotNone(store.hist1("rings_cross_profile"))
            self.assertIsNotNone(store.hist1("rings_corner_profile"))
            self.assertIsNotNone(store.hist1("rings_strips_profile"))
            self.assertIsNotNone(store.hist1("rings_custom_profile"))

            # Check Correlations (2D)
            store.cd("Expert-Monitoring/Correlations")
            self.assertIsNotNone(store.hist2("reta_vs_eta"))

            # Save and verify ROOT file persistence
            store.save()
            f = ROOT.TFile.Open(test_file, "READ")
            self.assertIsNotNone(f)
            self.assertIsNotNone(f.Get("Expert-Monitoring/ShowerShapes/reta"))
            f.Close()

    def test_monitoring_diff_logic(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
        from reco_monitoring_diff import compare_histograms, render_plot_figure, figure_to_base64

        h_test = ROOT.TH1F("h_test", "Test Histo;X;Count", 20, 0, 20)
        h_ref = ROOT.TH1F("h_ref", "Ref Histo;X;Count", 20, 0, 20)
        h_test.SetDirectory(0)
        h_ref.SetDirectory(0)

        for i in range(1, 21):
            h_test.SetBinContent(i, 10.0)
            h_ref.SetBinContent(i, 10.0)

        metrics = compare_histograms(h_test, h_ref)
        self.assertEqual(metrics["status"], "PASS")
        self.assertAlmostEqual(metrics["ks_pvalue"], 1.0, places=2)

        fig = render_plot_figure(h_test, h_ref, "TestPlot")
        b64 = figure_to_base64(fig)
        self.assertTrue(len(b64) > 100)

    def test_monitoring_cli_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_test = os.path.join(tmpdir, "expert_test.root")
            file_ref = os.path.join(tmpdir, "expert_ref.root")
            out_html = os.path.join(tmpdir, "report.html")
            out_pdf = os.path.join(tmpdir, "report.pdf")

            # Create test root file
            f1 = ROOT.TFile.Open(file_test, "RECREATE")
            top1 = f1.mkdir("Expert-Monitoring")
            d1 = top1.mkdir("ShowerShapes")
            d1.cd()
            h1 = ROOT.TH1F("reta", "reta", 10, 0, 1)
            for i in range(1, 11):
                h1.SetBinContent(i, 5.0)
            h1.Write()
            ROOT.SetOwnership(h1, False)
            f1.Close()

            # Create ref root file
            f2 = ROOT.TFile.Open(file_ref, "RECREATE")
            top2 = f2.mkdir("Expert-Monitoring")
            d2 = top2.mkdir("ShowerShapes")
            d2.cd()
            h2 = ROOT.TH1F("reta", "reta", 10, 0, 1)
            for i in range(1, 11):
                h2.SetBinContent(i, 5.0)
            h2.Write()
            ROOT.SetOwnership(h2, False)
            f2.Close()

            script_path = str(Path(__file__).parents[1] / "scripts" / "reco_monitoring_diff.py")
            cmd = f"python3 {script_path} -t {file_test} -r {file_ref} -o {out_html} --pdf {out_pdf}"
            import subprocess
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"reco_monitoring_diff failed: {res.stderr}")
            self.assertTrue(os.path.exists(out_html))
            self.assertTrue(os.path.exists(out_pdf))
            self.assertGreater(os.path.getsize(out_html), 500)
            self.assertGreater(os.path.getsize(out_pdf), 500)


if __name__ == "__main__":
    unittest.main()

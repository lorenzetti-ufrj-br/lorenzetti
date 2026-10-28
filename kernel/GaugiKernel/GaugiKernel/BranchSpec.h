#ifndef GaugiKernel_BranchSpec_h
#define GaugiKernel_BranchSpec_h

#include <string>
#include <vector>
#include <map>
#include "TTree.h"

namespace Gaugi {

  /**
   * @struct BranchSpec
   * @brief Specification of an output column/branch requested by user schema.
   */
  struct BranchSpec {
    std::string branchName; // Output column name, e.g. "cl_eta" or "ring_0"
    std::string fieldName;  // EDM field name, e.g. "eta" or "rings"
    int index{-1};          // Array index for indexed properties, e.g. 0 for "rings[0]", or -1
  };

  /**
   * @brief Helper to bind address or create branch if it does not exist yet.
   */
  template <typename T>
  inline void bindOrBranch(TTree *tree, const std::string &name, T *ptr) {
    if (!tree) return;
    if (tree->FindBranch(name.c_str())) {
      tree->SetBranchStatus(name.c_str(), 1);
      tree->SetBranchAddress(name.c_str(), ptr);
    } else {
      tree->Branch(name.c_str(), ptr);
    }
  }

  /**
   * @brief Parse a single target string like "CaloCluster#Clusters#eta" or "CaloRings#Rings#rings[0]"
   */
  inline bool parseTarget(const std::string &target, 
                          std::string &edm, 
                          std::string &key, 
                          std::string &field, 
                          int &index) 
  {
    index = -1;
    size_t firstHash = target.find('#');
    if (firstHash == std::string::npos) return false;
    size_t secondHash = target.find('#', firstHash + 1);
    if (secondHash == std::string::npos) return false;

    edm = target.substr(0, firstHash);
    key = target.substr(firstHash + 1, secondHash - firstHash - 1);
    std::string rawField = target.substr(secondHash + 1);

    // Check for array indexing like "rings[0]"
    size_t openBracket = rawField.find('[');
    size_t closeBracket = rawField.find(']');
    if (openBracket != std::string::npos && closeBracket != std::string::npos && closeBracket > openBracket) {
      field = rawField.substr(0, openBracket);
      std::string idxStr = rawField.substr(openBracket + 1, closeBracket - openBracket - 1);
      try {
        index = std::stoi(idxStr);
      } catch (...) {
        index = -1;
      }
    } else {
      field = rawField;
    }
    return true;
  }

  /**
   * @brief Parse an entire schema map {"cl_eta": "CaloCluster#Clusters#eta"}
   * into a grouped map: (edm, key) -> vector<BranchSpec>
   */
  inline std::map<std::pair<std::string, std::string>, std::vector<BranchSpec>>
  parseSchema(const std::map<std::string, std::string> &schema)
  {
    std::map<std::pair<std::string, std::string>, std::vector<BranchSpec>> groups;
    for (const auto &[outName, target] : schema) {
      std::string edm, key, field;
      int idx = -1;
      if (parseTarget(target, edm, key, field, idx)) {
        groups[{edm, key}].push_back({outName, field, idx});
      }
    }
    return groups;
  }

} // namespace Gaugi

#endif

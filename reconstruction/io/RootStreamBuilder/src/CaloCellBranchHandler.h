#ifndef CaloCellBranchHandler_h
#define CaloCellBranchHandler_h

#include "GenericBranchHandler.h"
#include "CaloCell/CaloCellContainer.h"
#include "CaloCell/CaloCellConverter.h"
#include "CaloCell/CaloDetDescriptorContainer.h"
#include <string>

namespace Gaugi {

  /**
   * @class CaloCellReadBuffer
   * @brief Specialized read buffer for CaloCellContainer with optional noise sigma filtering (ATLAS Run 4).
   */
  class CaloCellReadBuffer : public IReadBuffer {
  public:
    std::string key;
    std::vector<xAOD::CaloCell_t> *data;
    bool filterBySigma;
    float sigmaThreshold;
    std::string descriptorsKey;

    CaloCellReadBuffer(const std::string &k, bool filter, float threshold, const std::string &descKey)
      : key(k),
        data(new std::vector<xAOD::CaloCell_t>()),
        filterBySigma(filter),
        sigmaThreshold(threshold),
        descriptorsKey(descKey)
    {}

    virtual ~CaloCellReadBuffer() override {
      delete data;
      data = nullptr;
    }

    virtual StatusCode record(SG::EventContext &ctx) override {
      if (!data) {
        return StatusCode::FAILURE;
      }

      auto container = std::make_unique<xAOD::CaloCellContainer>();
      xAOD::CaloCellConverter cnv;

      if (filterBySigma) {
        SG::ReadHandle<xAOD::CaloDetDescriptorContainer> descContainer(descriptorsKey, ctx);
        bool hasDescriptors = descContainer.isValid();

        for (const auto &item_t : *data) {
          float cell_e = item_t.e;
          float sigma = 0.0f;
          if (hasDescriptors && item_t.descriptor_index < descContainer->size()) {
            const auto desc = descContainer->at(item_t.descriptor_index);
            if (desc) {
              sigma = desc->sigma();
            }
          }

          float threshold = (sigma > 0.0f) ? (sigmaThreshold * sigma) : 0.0f;
          if (cell_e <= threshold) {
            continue; // Filter out cell with E <= N*sigma
          }

          xAOD::CaloCell *cell = nullptr;
          cnv.convert(item_t, cell);
          if (cell) {
            container->push_back(cell);
          }
        }
      } else {
        // Standard unfiltered read
        for (const auto &item_t : *data) {
          xAOD::CaloCell *cell = nullptr;
          cnv.convert(item_t, cell);
          if (cell) {
            container->push_back(cell);
          }
        }
      }

      SG::WriteHandle<xAOD::CaloCellContainer> handle(key, ctx);
      handle.record(std::move(container));
      return StatusCode::SUCCESS;
    }
  };

  /**
   * @class CaloCellBranchHandler
   * @brief Specialized branch handler for CaloCellContainer with optional noise sigma filtering (ATLAS Run 4).
   *
   * Evaluates cell energies against electronic noise sigma (E > N*sigma)
   * independently on-the-fly during read. Surviving cells are recorded into StoreGate.
   */
  class CaloCellBranchHandler : public GenericBranchHandler<xAOD::CaloCellContainer,
                                                            xAOD::CaloCell_t,
                                                            xAOD::CaloCellConverter> {
  public:
    CaloCellBranchHandler(const std::string &key,
                          bool filterBySigma = false,
                          float sigmaThreshold = 2.0f,
                          const std::string &descriptorsKey = "CaloDetDescriptors")
      : GenericBranchHandler("CaloCellContainer", key),
        m_filterBySigma(filterBySigma),
        m_sigmaThreshold(sigmaThreshold),
        m_descriptorsKey(descriptorsKey)
    {}

    virtual ~CaloCellBranchHandler() = default;

    virtual std::unique_ptr<IReadBuffer> prepareRead(TTree *tree) const override {
      if (!tree) return nullptr;
      std::string bname = m_branchName;
      if (tree->GetAlias(bname.c_str())) {
        bname = std::string(tree->GetAlias(bname.c_str()));
      }
      if (!tree->FindBranch(bname.c_str())) {
        return nullptr;
      }
      auto buf = std::make_unique<CaloCellReadBuffer>(
          m_key, m_filterBySigma, m_sigmaThreshold, m_descriptorsKey);
      tree->SetBranchStatus(bname.c_str(), 1);
      tree->SetBranchAddress(bname.c_str(), &(buf->data));
      return buf;
    }

  private:
    bool m_filterBySigma;
    float m_sigmaThreshold;
    std::string m_descriptorsKey;
  };

} // namespace Gaugi

#endif

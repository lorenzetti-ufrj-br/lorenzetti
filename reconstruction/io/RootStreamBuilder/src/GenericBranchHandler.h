#ifndef GenericBranchHandler_h
#define GenericBranchHandler_h

#include "IBranchHandler.h"
#include "GaugiKernel/DataHandle.h"
#include <vector>
#include <memory>

namespace Gaugi {

  /**
   * @class TypedWriteBuffer
   * @brief Typed implementation of IWriteBuffer holding a heap-allocated std::vector<TStruct>.
   */
  template <typename TStruct>
  class TypedWriteBuffer : public IWriteBuffer {
  public:
    std::vector<TStruct> *data;

    TypedWriteBuffer() : data(new std::vector<TStruct>()) {}
    virtual ~TypedWriteBuffer() override {
      delete data;
      data = nullptr;
    }
  };

  /**
   * @class TypedReadBuffer
   * @brief Typed implementation of IReadBuffer holding read data and converting to TContainer in EventContext.
   */
  template <typename TContainer, typename TStruct, typename TConverter>
  class TypedReadBuffer : public IReadBuffer {
  public:
    std::string key;
    std::vector<TStruct> *data;

    TypedReadBuffer(const std::string &k)
      : key(k), data(new std::vector<TStruct>()) {}

    virtual ~TypedReadBuffer() override {
      delete data;
      data = nullptr;
    }

    virtual StatusCode record(SG::EventContext &ctx) override {
      if (!data) return StatusCode::FAILURE;

      auto container = std::make_unique<TContainer>();
      TConverter cnv;

      for (const auto &item_t : *data) {
        typename TContainer::base_type *obj = nullptr;
        cnv.convert(item_t, obj);
        if (obj) {
          container->push_back(obj);
        }
      }

      SG::WriteHandle<TContainer> handle(key, ctx);
      handle.record(std::move(container));
      return StatusCode::SUCCESS;
    }
  };

  /**
   * @class GenericBranchHandler
   * @brief Type-safe template implementing IBranchHandler for EDM container types.
   */
  template <typename TContainer, typename TStruct, typename TConverter>
  class GenericBranchHandler : public IBranchHandler {
  public:
    GenericBranchHandler(const std::string &typeName, const std::string &key)
      : m_typeName(typeName),
        m_key(key),
        m_branchName(typeName + "_" + key)
    {}

    virtual ~GenericBranchHandler() = default;

    virtual std::string typeName() const override { return m_typeName; }
    virtual std::string key() const override { return m_key; }
    virtual std::string branchName() const override { return m_branchName; }

    virtual std::unique_ptr<IReadBuffer> prepareRead(TTree *tree) const override {
      if (!tree) return nullptr;
      std::string bname = m_branchName;
      if (tree->GetAlias(bname.c_str())) {
        bname = std::string(tree->GetAlias(bname.c_str()));
      }
      if (!tree->FindBranch(bname.c_str())) {
        return nullptr;
      }
      auto buf = std::make_unique<TypedReadBuffer<TContainer, TStruct, TConverter>>(m_key);
      tree->SetBranchStatus(bname.c_str(), 1);
      tree->SetBranchAddress(bname.c_str(), &(buf->data));
      return buf;
    }

    virtual void bookBranch(TTree *tree) const override {
      if (!tree) return;
      std::vector<TStruct> dummy;
      tree->Branch(m_branchName.c_str(), &dummy);
      tree->ResetBranchAddresses();
    }

    virtual std::unique_ptr<IWriteBuffer> writeFromContext(TTree *tree, SG::EventContext &ctx) const override {
      if (!tree) return nullptr;
      auto buf = std::make_unique<TypedWriteBuffer<TStruct>>();
      tree->SetBranchAddress(m_branchName.c_str(), &(buf->data));

      SG::ReadHandle<TContainer> handle(m_key, ctx);
      if (handle.isValid()) {
        TConverter cnv;
        for (const auto obj : *handle) {
          if (!obj) continue;
          TStruct item_t;
          cnv.convert(obj, item_t);
          buf->data->push_back(item_t);
        }
      }

      return buf;
    }

  protected:
    std::string m_typeName;
    std::string m_key;
    std::string m_branchName;
  };

} // namespace Gaugi

#endif

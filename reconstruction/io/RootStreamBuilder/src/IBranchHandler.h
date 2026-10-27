#ifndef IBranchHandler_h
#define IBranchHandler_h

#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/EventContext.h"
#include "TTree.h"
#include <string>
#include <memory>

namespace Gaugi {

  /**
   * @class IWriteBuffer
   * @brief Polymorphic RAII write buffer holding per-event heap data during TTree filling.
   */
  class IWriteBuffer {
  public:
    virtual ~IWriteBuffer() = default;
  };

  /**
   * @class IReadBuffer
   * @brief Polymorphic RAII read buffer holding per-event heap data during TTree reading and StoreGate recording.
   */
  class IReadBuffer {
  public:
    virtual ~IReadBuffer() = default;

    /*! Convert read persistent data into EDM objects and record into EventContext */
    virtual StatusCode record(SG::EventContext &ctx) = 0;
  };

  /**
   * @class IBranchHandler
   * @brief Polymorphic interface to serialize and deserialize branches dynamically.
   */
  class IBranchHandler {
  public:
    virtual ~IBranchHandler() = default;

    /*! Return the EDM type name (e.g., "CaloClusterContainer", "ElectronContainer") */
    virtual std::string typeName() const = 0;

    /*! Return the StoreGate container key (e.g., "CaloClusters", "Electrons") */
    virtual std::string key() const = 0;

    /*! Return the formatted branch name ("<TypeName>_<Key>") */
    virtual std::string branchName() const = 0;

    /*! Prepare local read buffer and link branch address on tree */
    virtual std::unique_ptr<IReadBuffer> prepareRead(TTree *tree) const = 0;

    /*! Book branch for writing to TTree */
    virtual void bookBranch(TTree *tree) const = 0;

    /*! Alias for backwards compatibility */
    virtual void initWriteBranch(TTree *tree) { bookBranch(tree); }

    /*! Read container from EventContext, set branch address on tree, and return RAII write buffer */
    virtual std::unique_ptr<IWriteBuffer> writeFromContext(TTree *tree, SG::EventContext &ctx) const = 0;

    /*! Backwards compatibility */
    virtual void initReadBranch(TTree */*tree*/) {}
    virtual StatusCode readAndRecord(SG::EventContext &/*ctx*/) { return StatusCode::SUCCESS; }
    virtual void clear() {}
  };

} // namespace Gaugi

#endif

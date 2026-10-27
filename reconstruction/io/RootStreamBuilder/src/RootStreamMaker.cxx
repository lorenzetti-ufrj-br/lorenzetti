#include "RootStreamMaker.h"
#include "BranchHandlerFactory.h"

using namespace Gaugi;

RootStreamMaker::RootStreamMaker(std::string name)
  : IMsgService(name),
    Algorithm(),
    m_ntupleName("CollectionTree"),
    m_outputFile(""),
    m_itemList(),
    m_outputLevel(1),
    m_onlyRoI(false),
    m_etaWindow(0.4f),
    m_phiWindow(0.4f),
    m_truthKey("Particles"),
    m_cellHashes()
{
  declareProperty("TreeName",      m_ntupleName);
  declareProperty("NtupleName",    m_ntupleName); // alias for backwards compatibility
  declareProperty("ItemList",      m_itemList);
  declareProperty("OutputFile",    m_outputFile);
  declareProperty("OutputLevel",   m_outputLevel);
  declareProperty("OnlyRoI",       m_onlyRoI);
  declareProperty("EtaWindow",     m_etaWindow);
  declareProperty("PhiWindow",     m_phiWindow);
  declareProperty("TruthKey",      m_truthKey);
  declareProperty("InputTruthKey", m_truthKey);
  declareProperty("CellHashes",    m_cellHashes);
}

RootStreamMaker::~RootStreamMaker()
{
}

StatusCode RootStreamMaker::initialize()
{
  CHECK_INIT();
  setMsgLevel(m_outputLevel);
  return StatusCode::SUCCESS;
}

std::vector<std::unique_ptr<IBranchHandler>> RootStreamMaker::createHandlers() const
{
  std::vector<std::unique_ptr<IBranchHandler>> handlers;
  handlers.reserve(m_itemList.size());

  for (const auto &item : m_itemList) {
    if (item.empty()) continue;

    std::string typeName;
    std::string key;

    // Support Type#Key, Type/Key, or Type_Key
    size_t sepPos = item.find('#');
    if (sepPos == std::string::npos) {
      sepPos = item.find('/');
    }
    if (sepPos == std::string::npos) {
      sepPos = item.find('_');
    }

    if (sepPos == std::string::npos) {
      MSG_WARNING("Invalid item specification: '" << item << "'. Expected 'TypeName#Key'. Skipping.");
      continue;
    }

    typeName = item.substr(0, sepPos);
    key = item.substr(sepPos + 1);

    auto handler = BranchHandlerFactory::createHandler(
        typeName, key, m_onlyRoI, m_etaWindow, m_phiWindow, m_truthKey, m_cellHashes);
    if (handler) {
      handlers.push_back(std::move(handler));
    } else {
      MSG_ERROR("Unknown type '" << typeName << "' in item '" << item << "'. Cannot create branch handler.");
    }
  }

  return handlers;
}

StatusCode RootStreamMaker::bookHistograms(SG::EventContext &ctx) const
{
  auto store = ctx.getStoreGateSvc();
  if (!store) {
    MSG_FATAL("StoreGate service is null!");
    return StatusCode::FAILURE;
  }

  store->cd(); // Ensure gDirectory is root "/" of StoreGate file
  TTree *tree = store->tree(m_ntupleName);
  if (!tree) {
    tree = new TTree(m_ntupleName.c_str(), m_ntupleName.c_str());
    store->add(tree, true);
  }

  auto handlers = createHandlers();
  for (const auto &handler : handlers) {
    handler->bookBranch(tree);
  }

  return StatusCode::SUCCESS;
}

StatusCode RootStreamMaker::pre_execute(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamMaker::execute(SG::EventContext &/*ctx*/, const G4Step * /*step*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamMaker::execute(SG::EventContext &ctx, int /*evt*/) const
{
  return post_execute(ctx);
}

StatusCode RootStreamMaker::post_execute(SG::EventContext &ctx) const
{
  auto store = ctx.getStoreGateSvc();
  if (!store) {
    MSG_FATAL("StoreGate service is null!");
    return StatusCode::FAILURE;
  }

  store->cd();
  TTree *tree = store->tree(m_ntupleName);
  if (!tree) {
    if (bookHistograms(ctx).isFailure()) {
      return StatusCode::FAILURE;
    }
    tree = store->tree(m_ntupleName);
    if (!tree) {
      MSG_FATAL("Could not get or book TTree '" << m_ntupleName << "'");
      return StatusCode::FAILURE;
    }
  }

  auto handlers = createHandlers();
  std::vector<std::unique_ptr<IWriteBuffer>> buffers;
  buffers.reserve(handlers.size());

  for (const auto &handler : handlers) {
    buffers.push_back(handler->writeFromContext(tree, ctx));
  }

  tree->Fill();

  buffers.clear();
  tree->ResetBranchAddresses();

  return StatusCode::SUCCESS;
}

StatusCode RootStreamMaker::fillHistograms(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamMaker::finalize()
{
  return StatusCode::SUCCESS;
}

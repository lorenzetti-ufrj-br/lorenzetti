#include "RootStreamReader.h"
#include "BranchHandlerFactory.h"
#include "TObjArray.h"
#include "TBranch.h"

using namespace Gaugi;

RootStreamReader::RootStreamReader(std::string name)
  : IMsgService(name),
    Algorithm(),
    m_inputFile(""),
    m_ntupleName("CollectionTree"),
    m_outputLevel(1),
    m_filterBySigma(false),
    m_sigmaThreshold(2.0f),
    m_descriptorsKey("CaloDetDescriptors")
{
  declareProperty("InputFile",        m_inputFile);
  declareProperty("TreeName",         m_ntupleName);
  declareProperty("NtupleName",       m_ntupleName);
  declareProperty("OutputLevel",      m_outputLevel);
  declareProperty("FilterBySigma",    m_filterBySigma);
  declareProperty("SigmaThreshold",   m_sigmaThreshold);
  declareProperty("DescriptorsKey",   m_descriptorsKey);
}

RootStreamReader::~RootStreamReader()
{
}

StatusCode RootStreamReader::initialize()
{
  CHECK_INIT();
  setMsgLevel(m_outputLevel);
  return StatusCode::SUCCESS;
}

std::vector<std::unique_ptr<IBranchHandler>> RootStreamReader::createHandlers(TTree *tree) const
{
  std::vector<std::unique_ptr<IBranchHandler>> handlers;
  if (!tree) {
    return handlers;
  }

  TObjArray *branchList = tree->GetListOfBranches();
  if (!branchList) {
    MSG_WARNING("No branches found in TTree: " << m_ntupleName);
    return handlers;
  }

  for (int i = 0; i < branchList->GetEntries(); ++i) {
    TBranch *branch = dynamic_cast<TBranch*>(branchList->At(i));
    if (!branch) continue;

    std::string bname = branch->GetName();
    size_t sepPos = bname.find('_');
    if (sepPos == std::string::npos || sepPos == 0 || sepPos == bname.size() - 1) {
      MSG_DEBUG("Skipping branch with non-standard naming: " << bname);
      continue;
    }

    std::string typeName = bname.substr(0, sepPos);
    std::string key = bname.substr(sepPos + 1);

    auto handler = BranchHandlerFactory::createHandler(
        typeName, key, false, 0.4f, 0.4f, "Particles", {},
        m_filterBySigma, m_sigmaThreshold, m_descriptorsKey);
    if (handler) {
      MSG_DEBUG("Discovered branch '" << bname << "' -> Type: " << typeName << ", Key: " << key);
      handlers.push_back(std::move(handler));
    } else {
      MSG_DEBUG("No handler factory registered for type '" << typeName << "' (branch: " << bname << ")");
    }
  }

  // Ensure CaloDetDescriptorContainer is processed before CaloCellContainer
  std::stable_sort(handlers.begin(), handlers.end(), [](const auto &a, const auto &b) {
    bool a_desc = (a->typeName() == "CaloDetDescriptorContainer");
    bool b_desc = (b->typeName() == "CaloDetDescriptorContainer");
    if (a_desc && !b_desc) return true;
    if (!a_desc && b_desc) return false;
    return false;
  });

  return handlers;
}

StatusCode RootStreamReader::bookHistograms(SG::EventContext &ctx) const
{
  auto store = ctx.getStoreGateSvc();
  if (!store) {
    MSG_FATAL("StoreGate service is null in EventContext!");
    return StatusCode::FAILURE;
  }

  TFile *file = (TFile*)store->decorator("events");
  if (!file) {
    if (m_inputFile.empty()) {
      MSG_FATAL("InputFile property is empty!");
      return StatusCode::FAILURE;
    }

    file = new TFile(m_inputFile.c_str(), "READ");
    if (!file || file->IsZombie()) {
      MSG_FATAL("Could not open ROOT input file: " << m_inputFile);
      return StatusCode::FAILURE;
    }
    store->decorate("events", file);
  }

  TTree *tree = dynamic_cast<TTree*>(file->Get(m_ntupleName.c_str()));
  if (!tree) {
    MSG_FATAL("Could not find TTree with name '" << m_ntupleName << "' in file: " << m_inputFile);
    return StatusCode::FAILURE;
  }

  MSG_INFO("Opened file '" << m_inputFile << "' with " << tree->GetEntries() << " events.");
  return StatusCode::SUCCESS;
}

StatusCode RootStreamReader::pre_execute(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamReader::execute(SG::EventContext &/*ctx*/, const G4Step * /*step*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamReader::execute(SG::EventContext &ctx, int evt) const
{
  auto store = ctx.getStoreGateSvc();
  if (!store) {
    MSG_FATAL("StoreGate service is null in EventContext!");
    return StatusCode::FAILURE;
  }

  TFile *file = (TFile*)store->decorator("events");
  if (!file) {
    if (bookHistograms(ctx).isFailure()) {
      return StatusCode::FAILURE;
    }
    file = (TFile*)store->decorator("events");
    if (!file) {
      MSG_FATAL("Input TFile not found in EventContext StoreGate decorator 'events'!");
      return StatusCode::FAILURE;
    }
  }

  TTree *tree = dynamic_cast<TTree*>(file->Get(m_ntupleName.c_str()));
  if (!tree) {
    MSG_FATAL("Could not find TTree '" << m_ntupleName << "' in file: " << m_inputFile);
    return StatusCode::FAILURE;
  }

  auto handlers = createHandlers(tree);

  std::vector<std::unique_ptr<IReadBuffer>> buffers;
  buffers.reserve(handlers.size());

  for (const auto &handler : handlers) {
    buffers.push_back(handler->prepareRead(tree));
  }

  tree->GetEntry(evt);
  tree->ResetBranchAddresses();

  for (auto &buf : buffers) {
    if (buf) {
      if (buf->record(ctx).isFailure()) {
        MSG_WARNING("Failed to record container into StoreGate");
      }
    }
  }

  buffers.clear();
  return StatusCode::SUCCESS;
}

StatusCode RootStreamReader::post_execute(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamReader::fillHistograms(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamReader::finalize()
{
  return StatusCode::SUCCESS;
}

long long RootStreamReader::entries() const
{
  if (m_inputFile.empty()) return 0;
  std::unique_ptr<TFile> file(TFile::Open(m_inputFile.c_str(), "READ"));
  if (!file || file->IsZombie()) return 0;
  TTree *tree = dynamic_cast<TTree*>(file->Get(m_ntupleName.c_str()));
  long long n = tree ? tree->GetEntries() : 0;
  file->Close();
  return n;
}

long long RootStreamReader::entries(SG::EventContext &ctx) const
{
  auto store = ctx.getStoreGateSvc();
  if (store) {
    TFile *file = (TFile*)store->decorator("events");
    if (file) {
      TTree *tree = dynamic_cast<TTree*>(file->Get(m_ntupleName.c_str()));
      if (tree) return tree->GetEntries();
    }
  }
  return entries();
}

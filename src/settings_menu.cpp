// Offer the shared pause/display menu for this single-disc title too.
#include "mod_plugins.h"
#include "psx_menu_host.h"
#include "recomp_ui_psx_menu.h"

#if defined(RE1_QA_TOOLS)
namespace {
const PsxMenuHost* qa_host;
PsxMenuProvider qa_provider;
int qa_attach(void*, void* window, void* gl, const PsxMenuHost* host) {
    qa_host = host;
    const auto* base = recomp_ui_psx_menu_provider();
    return base->attach(base->ctx, window, gl, host);
}
void qa_detach(void*) {
    const auto* base = recomp_ui_psx_menu_provider();
    base->detach(base->ctx);
    qa_host = nullptr;
}
}
extern "C" const PsxMenuHost* re1_qa_settings_host() { return qa_host; }
#endif

PSX_MOD_CONSTRUCTOR(re1_settings_menu) {
#if defined(RE1_QA_TOOLS)
    qa_provider = *recomp_ui_psx_menu_provider();
    qa_provider.attach = qa_attach;
    qa_provider.detach = qa_detach;
    psx_menu_set_provider(&qa_provider);
#else
    psx_menu_set_provider(recomp_ui_psx_menu_provider());
#endif
}

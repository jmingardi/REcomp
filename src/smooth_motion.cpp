// Optional presentation-only mode. Guest code, clocks and saves stay stock.
#include "mod_plugins.h"

namespace {
void activate() {
    (void)psx_mod_request_frame_generation(60);
}
}

PSX_MOD_CONSTRUCTOR(re1_smooth_motion) {
    (void)psx_mod_register_activation_plugin("re1.smooth-motion", activate);
}

// QA-only SDL virtual gamepad. Exercises the host input path, never guest RAM.
#include <SDL3/SDL.h>
#include "mod_plugins.h"
#include "json11.hpp"
#include "psx_menu_host.h"
#include "consoles/psx/psx_pad_binds.h"
#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

extern "C" const PsxMenuHost* re1_qa_settings_host();

namespace {
SDL_JoystickID virtual_id;
SDL_Joystick* virtual_joystick;
std::string virtual_name;

int reply_json(const json11::Json& value, char* reply, int cap) {
    const auto text = value.dump();
    if (text.size() + 1 > static_cast<size_t>(cap)) {
        std::snprintf(reply, cap, "QA reply exceeds capacity");
        return 0;
    }
    std::snprintf(reply, cap, "%s", text.c_str());
    return 1;
}

int hostpad(const char* args, char* reply, int cap) {
    std::string error;
    // mod_cmd's legacy string reader retains JSON escapes. Hex avoids nesting
    // escaped quotes in that transport, without changing the shared protocol.
    std::string decoded;
    const std::string encoded = args ? args : "";
    const auto nibble = [](char c) -> int {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        return -1;
    };
    if (encoded.empty() || encoded.size() % 2)
        return reply_json(json11::Json::object{{"error", "Expected hex-encoded JSON"}}, reply, cap);
    for (size_t i = 0; i < encoded.size(); i += 2) {
        const int hi = nibble(encoded[i]), lo = nibble(encoded[i + 1]);
        if (hi < 0 || lo < 0) return reply_json(json11::Json::object{{"error", "Invalid hex"}}, reply, cap);
        decoded.push_back(static_cast<char>((hi << 4) | lo));
    }
    const auto input = json11::Json::parse(decoded, error);
    if (!error.empty()) return reply_json(json11::Json::object{{"error", error}}, reply, cap);
    const auto action = input["action"].string_value();
    if (action == "rebind" || action == "reset-bindings") {
        const auto* host = re1_qa_settings_host();
        if (!virtual_joystick || !host || !host->reload_bindings)
            return reply_json(json11::Json::object{{"error", "Need live virtual pad and attached settings host"}}, reply, cap);
        char guid[40] = {};
        SDL_GUIDToString(SDL_GetJoystickGUID(virtual_joystick), guid, sizeof guid);
        const std::string path = std::string(SDL_GetBasePath()) + "input.ini";
        if (action == "reset-bindings") rui_psx_pad_binds_reset(path.c_str(), guid);
        else {
            const int target = input["target"].int_value();
            const int source = SDL_GetGamepadButtonFromString(input["source"].string_value().c_str());
            if (target < 0 || target > 23 || source < 0)
                return reply_json(json11::Json::object{{"error", "Invalid mapping"}}, reply, cap);
            rui_psx_pad_binds_set(path.c_str(), guid, target, 1, source, 0);
        }
        host->reload_bindings();
    } else if (action == "detach") {
        if (virtual_joystick) SDL_CloseJoystick(virtual_joystick);
        if (virtual_id) SDL_DetachVirtualJoystick(virtual_id);
        virtual_joystick = nullptr;
        virtual_id = 0;
    } else if (action == "attach") {
        if (virtual_id) return reply_json(json11::Json::object{{"error", "Detach previous virtual pad first"}}, reply, cap);
        const auto profile = input["profile"].string_value();
        Uint16 vendor = 0, product = 0;
        if (profile == "xbox") { vendor = 0x045e; product = 0x02ea; }
        else if (profile == "dualshock") { vendor = 0x054c; product = 0x05c4; }
        else if (profile == "dualsense") { vendor = 0x054c; product = 0x0ce6; }
        else if (profile != "generic") return reply_json(json11::Json::object{{"error", "Unknown virtual profile"}}, reply, cap);
        virtual_name = "RE1 QA Virtual " + profile;
        SDL_VirtualJoystickDesc desc;
        SDL_INIT_INTERFACE(&desc);
        desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
        desc.vendor_id = vendor;
        desc.product_id = product;
        desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
        desc.nbuttons = SDL_GAMEPAD_BUTTON_COUNT;
        desc.axis_mask = (1u << SDL_GAMEPAD_AXIS_COUNT) - 1u;
        desc.button_mask = (1u << SDL_GAMEPAD_BUTTON_COUNT) - 1u;
        desc.name = virtual_name.c_str();
        virtual_id = SDL_AttachVirtualJoystick(&desc);
        virtual_joystick = virtual_id ? SDL_OpenJoystick(virtual_id) : nullptr;
        if (!virtual_joystick) {
            if (virtual_id) SDL_DetachVirtualJoystick(virtual_id);
            virtual_id = 0;
            return reply_json(json11::Json::object{{"error", SDL_GetError()}}, reply, cap);
        }
        // Triggers rest at the negative end; sticks remain centered.
        SDL_SetJoystickVirtualAxis(virtual_joystick, SDL_GAMEPAD_AXIS_LEFT_TRIGGER, -32768);
        SDL_SetJoystickVirtualAxis(virtual_joystick, SDL_GAMEPAD_AXIS_RIGHT_TRIGGER, -32768);
        SDL_UpdateJoysticks();
    } else if (action == "state") {
        if (!virtual_joystick) return reply_json(json11::Json::object{{"error", "No virtual pad"}}, reply, cap);
        for (int i = 0; i < SDL_GAMEPAD_BUTTON_COUNT; ++i) {
            bool down = false;
            for (const auto& button : input["buttons"].array_items()) {
                if (SDL_GetGamepadButtonFromString(button.string_value().c_str()) == i) down = true;
            }
            SDL_SetJoystickVirtualButton(virtual_joystick, i, down);
        }
        for (int i = 0; i < SDL_GAMEPAD_AXIS_COUNT; ++i) {
            int value = i >= SDL_GAMEPAD_AXIS_LEFT_TRIGGER ? -32768 : 0;
            const auto name = SDL_GetGamepadStringForAxis(static_cast<SDL_GamepadAxis>(i));
            if (name && !input["axes"][name].is_null()) value = input["axes"][name].int_value();
            SDL_SetJoystickVirtualAxis(virtual_joystick, i, static_cast<Sint16>(std::clamp(value, -32768, 32767)));
        }
        SDL_UpdateJoysticks();
    } else if (action != "list") {
        return reply_json(json11::Json::object{{"error", "Expected attach, state, detach or list"}}, reply, cap);
    }
    int count = 0;
    auto* ids = SDL_GetGamepads(&count);
    json11::Json::array devices;
    for (int i = 0; ids && i < count && i < 4; ++i) {
        const auto* name = SDL_GetGamepadNameForID(ids[i]);
        devices.push_back(json11::Json::object{{"id", static_cast<int>(ids[i])},
            {"name", name ? name : ""}, {"virtual", ids[i] == virtual_id},
            {"vendor", static_cast<int>(SDL_GetGamepadVendorForID(ids[i]))},
            {"product", static_cast<int>(SDL_GetGamepadProductForID(ids[i]))}});
    }
    SDL_free(ids);
    return reply_json(json11::Json::object{{"virtual_id", static_cast<int>(virtual_id)},
                                         {"devices", devices}, {"total", count}}, reply, cap);
}
}

PSX_MOD_CONSTRUCTOR(re1_register_qa_hostpad) {
    (void)psx_mod_register_command("re1.qa.hostpad", hostpad);
}

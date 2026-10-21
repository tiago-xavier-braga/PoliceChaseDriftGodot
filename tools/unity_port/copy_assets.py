"""Copy the media the Unity game uses into the Godot project, renamed to the project's conventions.

Run from anywhere: python tools/unity_port/copy_assets.py
The Unity project must be cloned into unity/PoliceChaseDrift/ with its Git LFS files pulled.
"""
import os
import re
import shutil

GODOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UNITY = os.path.join(GODOT, "unity", "PoliceChaseDrift", "Assets")

KITS = {
    "ThirdParty/Kenney City Kit Commercial 2.1/Meshes": "kenney_city_kit_commercial",
    "ThirdParty/Kenney City Kit Industrial 1.0/Meshes": "kenney_city_kit_industrial",
    "ThirdParty/Kenney City Kit Residential/Meshes": "kenney_city_kit_residential",
    "ThirdParty/Kenney City Kit Roads/Meshes": "kenney_city_kit_roads",
    "Art/Meshes/Cars": "kenney_car_kit",
}
# Only the meshes the scenes and prefabs reference (tools/unity_port/used_assets.py).
MODELS = {
    "kenney_city_kit_commercial": ["building-c", "building-d", "building-e", "building-f", "building-g"],
    "kenney_city_kit_industrial": ["building-f", "building-g", "building-h", "building-n",
                                   "building-p", "building-s", "detail-tank"],
    "kenney_city_kit_residential": [],
    "kenney_city_kit_roads": ["construction-barrier", "light-curved", "road-bend", "road-intersection-line",
                              "road-slant-curve", "road-straight"],
    "kenney_car_kit": ["ambulance", "delivery-flat", "police", "race", "sedan", "sedan-sports", "suv", "taxi",
                       "truck-flat", "van"],
}
FILES = {
    "Art/Meshes/Npc/Police.fbx": "assets/models/characters/police.fbx",
    "Art/Meshes/Npc/Thief.fbx": "assets/models/characters/thief.fbx",
    "ThirdParty/Kenney Mini Characters/Models/FBX format/Textures/colormap.png":
        "assets/textures/txt_kenney_mini_characters.png",
    "Art/Textures/Cars/TXT_ColorMap.png": "assets/textures/txt_kenney_car_kit.png",
    "Art/Textures/Cars/TXT_ColorMap_1.png": "assets/textures/txt_kenney_car_kit_variant_2.png",
    "Art/Textures/Cars/TXT_ColorMap_2.png": "assets/textures/txt_kenney_car_kit_variant_3.png",
    "ThirdParty/Kenney City Kit Commercial 2.1/Textures/TXT_CityKitCommercial_Basemap.png":
        "assets/textures/txt_kenney_city_kit_commercial.png",
    "ThirdParty/Kenney City Kit Industrial 1.0/Textures/TXT_CityKitIndustrial.png":
        "assets/textures/txt_kenney_city_kit_industrial.png",
    "ThirdParty/Kenney City Kit Residential/Textures/TXT_CityKitResidentialA.png":
        "assets/textures/txt_kenney_city_kit_residential_a.png",
    "ThirdParty/Kenney City Kit Residential/Textures/TXT_CityKitResidentialC.png":
        "assets/textures/txt_kenney_city_kit_residential_c.png",
    "ThirdParty/Kenney City Kit Roads/Textures/TXT_CityKitRoads.png": "assets/textures/txt_kenney_city_kit_roads.png",
    "ThirdParty/Free Stylized Skybox/Panoramic/Textures/Sky_Anime_11_morning_a.png":
        "assets/textures/txt_sky_morning.png",
    "ThirdParty/AureDevGames/Water Stylized Shader Orto & Perspective Camera/Textures/Procedural/"
    "voronoiAguaSubstance2 1.png": "assets/textures/txt_water_voronoi.png",
    "ThirdParty/AureDevGames/Water Stylized Shader Orto & Perspective Camera/Textures/Procedural/perlinNoise.png":
        "assets/textures/txt_water_noise.png",
    "Art/Textures/Ui/TXT_PackUI.png": "assets/textures/ui/txt_ui_pack.png",
    "Art/Textures/Ui/TXT_PackIcons.png": "assets/textures/ui/txt_ui_icons.png",
    "Art/Textures/Ui/TXT_Spinner.png": "assets/textures/ui/txt_ui_spinner.png",
    "Art/Fonts/LuckiestGuy-Regular.ttf": "assets/fonts/luckiest_guy.ttf",
    "Audio/SoundEffects/Car/SFX_CarEngine.wav": "assets/audio/sfx_car_engine.wav",
    "Audio/SoundEffects/SFX_ImpactPlank.ogg": "assets/audio/sfx_impact_plank.ogg",
    "Audio/SoundEffects/SFX_ImpactPlate.ogg": "assets/audio/sfx_impact_plate.ogg",
    "Audio/SoundEffects/SFX_PoliceSiren.mp3": "assets/audio/sfx_police_siren.mp3",
    "Audio/VoiceOvers/SFX_Smille.wav": "assets/audio/sfx_voice_smile.wav",
    "Audio/VoiceOvers/SFX_SpeakingNervously.wav": "assets/audio/sfx_voice_speaking_nervously.wav",
    "Audio/VoiceOvers/SFX_Sprint.wav": "assets/audio/sfx_voice_sprint.wav",
    "Audio/Musics/Overboard.mp3": "assets/audio/music_overboard.mp3",
    "XaviGames/UICore/Clip/SFX_ButtonClick.ogg": "assets/audio/sfx_button_click.ogg",
    "XaviGames/UICore/Clip/SFX_ButtonRelease.ogg": "assets/audio/sfx_button_release.ogg",
}
KENNEY_LICENSE = """{name}

Created by Kenney (www.kenney.nl), released under Creative Commons Zero (CC0):
http://creativecommons.org/publicdomain/zero/1.0/
"""


def snake(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def copy(src, dst):
    full = os.path.join(GODOT, dst)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    shutil.copyfile(os.path.join(UNITY, src), full)
    with open(full, "rb") as fh:
        assert not fh.read(40).startswith(b"version https://git-lfs"), "run git lfs pull in the Unity clone: " + src


def main():
    for folder, kit in KITS.items():
        for name in MODELS[kit]:
            copy("%s/%s.fbx" % (folder, name), "assets/models/%s/%s.fbx" % (kit, snake(name)))
        if MODELS[kit]:
            with open(os.path.join(GODOT, "assets/models", kit, "license.txt"), "w") as fh:
                fh.write(KENNEY_LICENSE.format(name=kit.replace("_", " ").title()))
    for src, dst in FILES.items():
        copy(src, dst)
    print("copied", sum(len(v) for v in MODELS.values()) + len(FILES), "files")


if __name__ == "__main__":
    main()

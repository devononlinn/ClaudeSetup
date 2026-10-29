"""Relevance classifier: core_prep / bushcraft / off_topic, plus English flag. Keyword rules, title + description."""
import re
import unicodedata

CORE = re.compile(
    r"prepper|\bprepping (for|101|on a budget|tips|list|supplies|items)|\bprep(ping)? for (war|disaster|collapse|"
    r"emergenc|crisis|shtf|hard times|the worst|famine|blackout|hurricane|earthquake|wildfire|winter storm)|"
    r"emergency (kit|preparedness|supplies|supply|food|water|bag|backpack|plan|prep|radio|power|generator)|"
    r"\bbug[- ]?out|\bgo[- ]?bag\b.{0,40}(emergenc|evacuat|disaster|surviv|prep)|(emergenc|evacuat|disaster|surviv|prep).{0,40}\bgo[- ]?bag\b|"
    r"72[- ]?h(ou)?r|stockpil|\bblackout|power outage|power (is|goes|went) out|without power|lose power|"
    r"\bgrid (down|goes down|fail|collapse|is going down|emergency)|power grid|grid[- ]down|\bemp\b|solar flare|"
    r"\bshtf\b|\bteotwawki\b|doomsday (prep|bunker|plan|scenario)|\bbunker\b|\bfamine\b|food shortage|"
    r"(long[- ]term|emergency|survival) food|food storage|freeze[- ]dri|\bmre\b|mylar|water storage|"
    r"(hurricane|earthquake|wildfire|flood|tornado|winter storm|disaster|typhoon|tsunami).{0,40}(prep|ready|kit|"
    r"evacuat|surviv|supplies|plan|safe|warning|checklist)|(prep|ready|kit|evacuat|surviv|supplies|plan|safe)"
    r".{0,40}(hurricane|earthquake|wildfire|flood|tornado|winter storm|disaster)|evacuat|\bfema\b|red cross|"
    r"survive (the|a|an|hard|any|when|if|after|without)|survival (rules|plan|tips for (the )?(city|home))|"
    r"collapse|\bcrisis\b.{0,30}(prep|surviv|stock|buy)|before (it'?s too late|the collapse|shelves)|"
    r"disappear(ing)? from shel|\bgenerator\b|home (defense|security) .{0,20}(emergenc|shtf)|"
    r"emergency food|(storm|freeze|froze|winter).{0,30}(state|grid|power)|weather prep|survival (kit|gear|items|supplies|rifle|tips)|\bready\.gov|nuclear (war|attack|fallout|bomb).{0,40}(surviv|prep)|fallout shelter|potassium iodide",
    re.I)
OFF = re.compile(
    r"meal ?prep|recipe|\bcooking\b|#cooking|breakfast|lunch ?box|snack|avengers|marvel|\bmcu\b|loki|"
    r"makeup|\bhair\b|braid|school ?bag|backpack for (the )?(new )?school|back ?to ?school|birkin|hermes|"
    r"too good to go|marathon|concrete|\bnfl\b|golf|hospital bag|give birth|period kit|teen girls|"
    r"roblox|minecraft|fortnite|\bgta\b|video ?game|gameplay|\bplays?\b.{0,10}\bgame|fallout (4|76|new vegas|show|season)|"
    r"skin ?care|\bnails?\b|press on|wedding|\bpregnan|\bpill\b|diy project|handyman|home repair|halloween|christmas|thanksgiving|last day on earth|\balf\b|unwanted ?72|pharmacy|medicose", re.I)
WILD = re.compile(r"bushcraft|log cabin|\bforest\b|jungle|rainforest|primitive|\btrap\b|wild boar|wilderness|"
                  r"\bdugout\b|treehouse|\bcave\b|in the wild\b|survival (house|skills?)\b", re.I)
BUSH = re.compile(r"bushcraft|log cabin|survival (house|skills?|shelter)|\bshelter\b|primitive|\bcamping\b|"
                  r"\bforest\b|jungle|wilderness|\bdugout\b|treehouse|\btrap\b|off[- ]?grid|homestead|\bcabin\b", re.I)


def is_english(title, snippet):
    lang = (snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage") or "").lower()
    if lang and not lang.startswith("en") and lang != "zxx":
        return False
    letters = [c for c in title if unicodedata.category(c).startswith("L")]
    if not letters:
        return True
    latin = sum(1 for c in letters if "LATIN" in unicodedata.name(c, ""))
    if latin / len(letters) < 0.7:
        return False
    # common non-English latin-script titles that lack a language tag
    return not re.search(r"\b(prepara|mochila|emergencia|sismo|plecak|ewakuac|notfall|préparez|d'urgence|"
                         r"inondation|kryzys|terremoto|supervivencia|rucksack)\w*", title, re.I)


def classify(title, desc):
    t = title
    td = title + " " + desc[:300]
    if OFF.search(t):
        return "off_topic"
    if WILD.search(t):
        return "bushcraft"
    if CORE.search(t):
        return "core_prep"
    if BUSH.search(t) or BUSH.search(td) and re.search(r"#?(survival|bushcraft)", td, re.I):
        return "bushcraft"
    if CORE.search(td) and not OFF.search(td):
        return "core_prep"
    if re.search(r"\bsurviv", t, re.I):
        return "bushcraft"
    return "off_topic"

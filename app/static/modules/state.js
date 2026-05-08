export const DRAFT_STORAGE_KEY = "mtg-deck-analyzer-draft";
export const CARD_DENSITY_STORAGE_KEY = "mtg-deck-analyzer-card-density";

export const SAMPLE_DECKS = {
  "commander-spellslinger": {
    name: "Baral Spellslinger",
    format: "commander",
    commander: "Baral, Chief of Compliance",
    decklist: `1 Sol Ring
1 Arcane Signet
1 Command Tower
1 Thought Vessel
1 Mind Stone
1 Counterspell
1 Arcane Denial
1 Negate
1 Swan Song
1 Pongify
1 Rapid Hybridization
1 Reality Shift
1 Cyclonic Rift
1 Wash Away
1 Brainstorm
1 Ponder
1 Preordain
1 Opt
1 Frantic Search
1 Treasure Cruise
1 Dig Through Time
1 Windfall
1 Behold the Multiverse
1 Fact or Fiction
1 Mystic Remora
1 Rhystic Study
1 Search for Azcanta
1 Metallurgic Summonings
1 Talrand, Sky Summoner
1 Murmuring Mystic
1 Archmage Emeritus
1 Storm-Kiln Artist
1 Snapcaster Mage
1 Jace's Sanctum
1 Primal Amulet
1 Sapphire Medallion
1 Lightning Greaves
1 Reliquary Tower
1 Mystic Sanctuary
1 Castle Vantress
31 Island
1 Command Beacon
1 Otawara, Soaring City
1 Inventors' Fair
1 War Room
1 Lonely Sandbar
1 Myriad Landscape
1 Emergence Zone
1 Temple of the False God
1 Ghost Quarter
1 Strip Mine
1 Blast Zone
1 Field of Ruin
1 Sea Gate Restoration
1 Commit // Memory
1 Blue Sun's Zenith
1 Stroke of Genius
1 Narset's Reversal
1 Impulse
1 Solve the Equation
1 Fabricate
1 Resculpt
1 Capsize
1 Time Warp
1 Mystic Confluence
1 Force of Will
1 Force of Negation
1 Fierce Guardianship
1 Misdirection
1 Disallow
1 Spell Swindle
1 Aetherize
1 Evacuation
1 Digsite Engineer
1 Teferi's Ageless Insight
1 Hullbreaker Horror
1 Shark Typhoon
1 Metallurgic Summonings
1 High Tide
1 Turnabout
1 Snap
1 Unwind
1 Rewind
1 Mana Drain
1 Spell Pierce
1 Delay
1 Consider
1 Serum Visions
1 Gitaxian Probe
1 Secrets of the Golden City
1 Treasure Map
1 Midnight Clock
1 Bident of Thassa`,
    sideboard: "",
  },
  "modern-burn": {
    name: "Modern Burn Snapshot",
    format: "modern",
    commander: "",
    decklist: `4 Lightning Bolt
4 Lava Spike
4 Rift Bolt
4 Skewer the Critics
4 Monastery Swiftspear
4 Goblin Guide
4 Eidolon of the Great Revel
4 Boros Charm
4 Searing Blaze
4 Roiling Vortex
2 Skullcrack
2 Lightning Helix
4 Sacred Foundry
4 Inspiring Vantage
4 Sunbaked Canyon
4 Arid Mesa
3 Mountain
1 Fiery Islet`,
    sideboard: `2 Path to Exile
2 Smash to Smithereens
2 Sanctifier en-Vec
2 Deflecting Palm
2 Rest in Peace
2 Exquisite Firecraft
2 Skullcrack
1 Wear // Tear`,
  },
  "pioneer-spirits": {
    name: "Azorius Spirits Snapshot",
    format: "pioneer",
    commander: "",
    decklist: `4 Mausoleum Wanderer
4 Spectral Sailor
4 Supreme Phantom
4 Rattlechains
4 Shacklegeist
4 Spell Queller
3 Skyclave Apparition
2 Cemetery Illuminator
4 Curious Obsession
4 Geistlight Snare
4 Lofty Denial
2 Slip Out the Back
4 Hallowed Fountain
4 Seachrome Coast
4 Adarkar Wastes
4 Mutavault
4 Hengegate Pathway
3 Island
2 Plains`,
    sideboard: `2 Portable Hole
2 Destroy Evil
2 Rest in Peace
2 Wedding Announcement
2 Mystical Dispute
2 Knockout Blow
2 Extraction Specialist
1 Settle the Wreckage`,
  },
};

export const appState = {
  analysis: null,
  cards: {
    mainboard: [],
    sideboard: [],
  },
  ui: {
    highlightedSupportCards: [],
    selectedArchetypeName: "",
    compactCardView: window.localStorage.getItem(CARD_DENSITY_STORAGE_KEY) === "compact",
    cardFilter: "",
    cardSort: "name",
    cardSortDirection: "asc",
  },
};


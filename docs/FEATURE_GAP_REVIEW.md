## Feature Comparison & Enhancement Targets

### Competitive Snapshot
| Capability | AI Tuner Agent | Holley EFI | Haltech | MoTeC | RaceCapture Pro | Dragy |
|------------|----------------|-----------|---------|-------|-----------------|-------|
| Multi-ECU ingest (OBD, CAN, RaceCapture, Holley, MoTeC, Link, AEM...) | ✅ | ❌ (Holley only) | ❌ (Haltech only) | ⚠️ (MoTeC ecosystem) | ⚠️ (RaceCapture HW) | ❌ |
| Live AI copilot (RAG + conversational advisor) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Predictive diagnostics & health scoring | ✅ | ❌ | ❌ | ⚠️ basic limits | ❌ | ❌ |
| Enhanced telemetry graphing (multi-axis, FFT, math channels, export) | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ |
| Synchronized video overlays | ✅ | ❌ | ❌ | ⚠️ plugins | ⚠️ optional | ⚠️ |
| Remote/cloud sync & voice alerts | ✅ | ⚠️ manual | ⚠️ manual | ⚠️ manual | ⚠️ | ❌ |
| Pricing / hardware | Commodity Pi 5 / Windows | Proprietary | Proprietary | Proprietary | Dedicated logger | Standalone GPS puck |

### Vendor Strength Highlights
- **MoTeC**: Deep motorsport math channels, pro-level lap simulation, advanced traction/launch strategies.
- **Holley / Haltech**: Tight ECU integration, closed-loop boost and traction tables baked into firmware editors.
- **RaceCapture**: Solid live telemetry streaming but minimal AI guidance.
- **Dragy**: Simple UX for straight-line metrics, no tuning context.

### Opportunities for AI Tuner Agent
1. **Setup Intelligence Layer**  
   - Blend race engineer heuristics with our AI advisor.  
   - Provide quick suspension/aero/tire suggestions triggered directly inside chat.

2. **Theoretical Lap & Condition-Based Guidance (roadmap)**  
   - Combine lap delta calculator with setup assistant for “what-if” adjustments.  
   - Partners already highlight predictive laps; integrating with advisor keeps differentiator.

3. **Vendor-aware Recommendations**  
   - Detect when users mention Holley/MoTeC and respond with integration tips + value adds.

### Actions in this Update
1. **Documented competitive deltas** (this file) for quick reference during planning.
2. **Implemented Race Setup Recommender service** feeding curated drag/road race/endurance setups into the AI advisor so users instantly receive actionable suggestions when they ask for handling or traction help.

### Next Review Checklist
- Validate setup suggestions with more telemetry inputs (tire temps, g-loads).
- Expand comparison grid with AiM Solo, HP Tuners, FuelTech.
- Pair future roadmap items (predictive lap, OTA updates) with customer interviews.


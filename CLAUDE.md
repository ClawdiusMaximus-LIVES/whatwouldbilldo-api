# What Would Bill Do? — iOS App

## Identity
- **App Name:** What Would Bill Do?
- **Bundle ID:** com.whatwouldbilldo.app
- **Apple Team ID:** 7BW79QC9WM
- **GitHub:** ClawdiusMaximus-LIVES/whatwouldbilldo-ios
- **App Group:** group.com.whatwouldbilldo.app.shared
- **Deployment Target:** iOS 17.0
- **Swift Version:** Swift 6 (strict concurrency enabled)
- **Production API:** https://api.whatwouldbilldo.com
- **Dev API:** http://localhost:8000

## What This App Is
An AI-powered advisor grounded in Bill W.'s public domain writings. Users ask questions;
the app calls a FastAPI backend that retrieves relevant passages from the 1939 Big Book
and Bill's other public domain texts, then responds in Bill W.'s voice with citations.

The iOS app is a **pure API client** — no local corpus, no local AI. All intelligence
lives in the FastAPI backend. The app's job is to make the conversation feel like
receiving a letter, not using a chatbot.

## Tech Stack
- SwiftUI + Swift 6 + @Observable (no ObservableObject)
- SwiftData for local persistence (messages, conversations)
- URLSession async/await for API calls
- StoreKit 2 for IAP
- Superwall for paywall A/B testing (v1.1 — placeholder in v1)
- WidgetKit for home screen widget
- UserDefaults (App Group suite) for widget data sharing

## Design System
- **Primary background:** Parchment #F5EDD6
- **Accent:** Amber #C8860A
- **Text:** LexiconText #2C1810
- **Secondary text:** SaddleBrown #8B4513
- **Border/gold:** AgedGold #C4A96A
- **Crisis:** CrisisRed #E53935
- **Serif font:** EB Garamond (imported via SwiftUI custom font)
- **System font:** SF Pro (default)
- **Corner radius:** 16pt cards, 12pt buttons, pill CTAs
- **Mode:** Light mode only for v1 — force with .preferredColorScheme(.light)

## Monetization
- **Free tier:** 3 conversations, then hard paywall
- **Weekly:** $4.99 — com.whatwouldbilldo.app.weekly
- **Monthly:** $12.99 — com.whatwouldbilldo.app.monthly
- **Yearly:** $59.99 — com.whatwouldbilldo.app.yearly
- **Paywall trigger event (Superwall):** "bill_limit_reached"
- **Note:** Superwall is v1.1. In v1, show a native paywall sheet when limit is hit.

## API Endpoints
```
POST /ask
  Body: { "message": "...", "conversation_history": [...] }
  Returns: { "response": "...", "citations": [...], "crisis": bool, "crisis_message": "...", "crisis_resources": [...] }

GET /health
  Returns: { "status": "ok", "passages_count": 4821 }

GET /daily-reflection
  Returns: { "passage": "...", "source": "...", "reflection": "..." }
```

## AppState (UserDefaults keys)
- `isOnboardingComplete` Bool
- `sobrietyDate` Date? (optional)
- `freeConvosUsed` Int (0–3, then paywall)
- `isSubscribed` Bool

## SwiftData Models
```swift
@Model class Message {
    var id: UUID
    var role: String      // "user" or "bill"
    var content: String
    var citations: String // JSON array stored as string
    var timestamp: Date
}

@Model class Conversation {
    var id: UUID
    var startedAt: Date
    @Relationship(deleteRule: .cascade) var messages: [Message]
}
```

## App Structure
```
WhatWouldBillDo-iOS/
├── project.yml                    # xcodegen config
├── CLAUDE.md                      # This file
├── WhatWouldBillDo/
│   ├── WhatWouldBillDoApp.swift   # @main, .modelContainer
│   ├── ContentView.swift          # Onboarding gate → TabView
│   ├── AppState.swift             # @Observable, UserDefaults
│   ├── Models/
│   │   ├── Message.swift          # SwiftData @Model
│   │   ├── Conversation.swift     # SwiftData @Model
│   │   └── APIModels.swift        # Codable request/response structs
│   ├── Services/
│   │   ├── APIClient.swift        # URLSession async/await
│   │   ├── PurchaseManager.swift  # StoreKit 2
│   │   └── NotificationManager.swift
│   ├── Features/
│   │   ├── Onboarding/
│   │   │   └── OnboardingView.swift
│   │   ├── Chat/
│   │   │   ├── ChatView.swift
│   │   │   ├── ChatViewModel.swift
│   │   │   ├── BillMessageView.swift
│   │   │   ├── UserMessageView.swift
│   │   │   ├── MessageInputView.swift
│   │   │   └── CrisisView.swift
│   │   ├── DailyReflection/
│   │   │   └── DailyReflectionView.swift
│   │   └── Settings/
│   │       └── SettingsView.swift
│   └── Resources/
│       └── Assets.xcassets
└── WhatWouldBillDoWidget/
    └── WhatWouldBillDoWidget.swift
```

## Copyright Rules — CRITICAL
- ONLY cite: Alcoholics Anonymous (1939), Original Manuscript (1938), AA Grapevine articles (early), personal letters, talk transcripts
- NEVER display or reference: Twelve Steps and Twelve Traditions (1952), As Bill Sees It (1967)
- If a citation from the API contains either forbidden work, suppress it in the UI silently
- The app is NOT affiliated with Alcoholics Anonymous World Services, Inc.

---

# SESSION PROMPTS — Run in Order

## SESSION 1: Project Scaffold + xcodegen + GitHub + Base App
**Time:** ~45 min | **Test:** Open in Xcode, build succeeds, runs on simulator before S2

```
# WWBD iOS — Session 1: Project Scaffold
# Run from: ~/Developer/ (or wherever you keep iOS projects)
# Goal: Working Xcode project that builds and runs on simulator

Create an iOS app called "What Would Bill Do?" using xcodegen.

## Project Setup

1. Create directory: WhatWouldBillDo-iOS/
2. Initialize git repo and push to GitHub as ClawdiusMaximus-LIVES/whatwouldbilldo-ios (public repo)
3. Create project.yml for xcodegen with:
   - Bundle ID: com.whatwouldbilldo.app
   - Apple Team ID: 7BW79QC9WM
   - Deployment target: iOS 17.0
   - Swift 6 mode (SWIFT_STRICT_CONCURRENCY = complete in build settings)
   - App Group entitlement: group.com.whatwouldbilldo.app.shared
   - Push Notifications capability
   - In-App Purchase capability

4. Run: xcodegen generate

## App Structure — Create these files

WhatWouldBillDoApp.swift:
- @main App struct
- Add .modelContainer(for: [Conversation.self, Message.self]) to WindowGroup
- Force light mode: .preferredColorScheme(.light) on root view

AppState.swift:
- @Observable class AppState
- Properties: isOnboardingComplete: Bool, sobrietyDate: Date?, freeConvosUsed: Int, isSubscribed: Bool
- Load/save all properties from UserDefaults
- func canSendMessage() -> Bool { isSubscribed || freeConvosUsed < 3 }

ContentView.swift:
- If !appState.isOnboardingComplete → show OnboardingView
- Else → show TabView with 3 tabs: Chat (bubble icon), Reflection (book.fill icon), Settings (gear icon)

Models/Message.swift:
- @Model class Message: id UUID, role String, content String, citations String (JSON), timestamp Date

Models/Conversation.swift:
- @Model class Conversation: id UUID, startedAt Date, @Relationship(deleteRule: .cascade) messages: [Message]

Models/APIModels.swift:
- AskRequest: Codable { message: String, conversation_history: [[String:String]] }
- AskResponse: Codable { response: String?, citations: [Citation]?, crisis: Bool, crisis_message: String?, crisis_resources: [[String:String]]? }
- Citation: Codable { source: String, chapter: String?, title: String?, similarity: Double? }
- DailyReflectionResponse: Codable { passage: String, source: String, reflection: String }

## Color System — Define in Assets.xcassets as named colors

- ParchmentBackground: #F5EDD6
- OldPaper: #EDD9A3
- AmberAccent: #C8860A
- LexiconText: #2C1810
- SaddleBrown: #8B4513
- AgedGold: #C4A96A
- CrisisRed: #E53935

Add a solid amber square as placeholder app icon (real icon comes in S10).

## Verify
- xcodegen generate
- Open in Xcode, build for iPhone 15 Pro simulator — no crashes
- App should launch and show a placeholder or blank ContentView

git add -A && git commit -m "S1: Project scaffold, xcodegen, SwiftData models, app structure" && git push origin main
```

---

## SESSION 2: API Client + Networking Layer
**Time:** ~30 min | **Test:** Unit test the client (no device testing needed)

```
# WWBD iOS — Session 2: Networking Layer
# Run from: WhatWouldBillDo-iOS/ project root
# Goal: APIClient that talks to the FastAPI backend

Create Services/APIClient.swift.

@Observable class APIClient {
    static let shared = APIClient()

    #if DEBUG
    let baseURL = "http://localhost:8000"
    #else
    let baseURL = "https://api.whatwouldbilldo.com"
    #endif

    func askBill(message: String, history: [[String:String]]) async throws -> AskResponse
    func checkHealth() async throws -> Bool
    func getDailyReflection() async throws -> DailyReflectionResponse
}

## Implementation requirements:
- URLSession.shared with async/await throughout
- Header on all requests: Content-Type: application/json
- Header: X-App-Key: wwbd-ios-v1
- URLSession timeout: 30 seconds (Bill responses take 2-8 seconds)
- APIError enum: serverError(Int), noNetwork, decodingError, timeout
- Daily reflection: check UserDefaults for today's cache before making network call

## DailyReflectionCache:
- Struct: date Date, passage String, source String, reflection String
- Stored as JSON in UserDefaults key "dailyReflectionCache"
- isFresh() -> Bool: returns true if date is today

## Quick test (add to a preview or test):
- Call checkHealth() → print result to console
- Call getDailyReflection() → print first 80 chars of reflection

git add -A && git commit -m "S2: APIClient async/await, daily reflection cache, health check" && git push origin main
```

---

## SESSION 3: StoreKit 2 + Purchase Manager
**Time:** ~45 min | **Test:** 🧪 StoreKit products must load in sandbox before S4

```
# WWBD iOS — Session 3: StoreKit 2
# IAP Product IDs (must match App Store Connect exactly):
#   com.whatwouldbilldo.app.weekly   — $4.99/week
#   com.whatwouldbilldo.app.monthly  — $12.99/month
#   com.whatwouldbilldo.app.yearly   — $59.99/year

Create Services/PurchaseManager.swift using StoreKit 2.

@Observable class PurchaseManager {
    static let shared = PurchaseManager()
    var products: [Product] = []
    var isSubscribed: Bool = false
    var activeProductID: String? = nil

    let productIDs = [
        "com.whatwouldbilldo.app.weekly",
        "com.whatwouldbilldo.app.monthly",
        "com.whatwouldbilldo.app.yearly"
    ]

    func loadProducts() async
    func purchase(_ product: Product) async throws -> Bool
    func restorePurchases() async throws
    func updateSubscriptionStatus() async
    func listenForTransactions()  // Transaction.updates loop, call in init
}

## CRITICAL: Verification pattern — no #if DEBUG bypasses ever:
    let result = try await product.purchase()
    switch result {
    case .success(let verification):
        switch verification {
        case .verified(let transaction):
            await transaction.finish()
            isSubscribed = true
            return true
        case .unverified:
            return false
        }
    case .userCancelled, .pending:
        return false
    }

## updateSubscriptionStatus() pattern:
    for await result in Transaction.currentEntitlements {
        if case .verified(let transaction) = result {
            if !transaction.isExpired && !transaction.isRevoked {
                isSubscribed = true
                activeProductID = transaction.productID
            }
        }
    }
    // Also update AppState.isSubscribed to match

## StoreKit Configuration File:
Create WWBD_StoreKit.storekit in project root with all 3 subscription products.
Add to scheme: Edit Scheme → Run → Options → StoreKit Configuration → WWBD_StoreKit.storekit

## Test:
- Run in simulator with StoreKit config
- Products load with correct names and prices
- Test purchase with sandbox — isSubscribed goes true
- Restore purchases — status persists after app restart

git add -A && git commit -m "S3: StoreKit 2 PurchaseManager, sandbox config, 3 IAP products" && git push origin main
```

---

## SESSION 4: Onboarding Flow
**Time:** ~60 min | **Test:** 🧪 Test on real device before building chat

```
# WWBD iOS — Session 4: Onboarding Flow
# Goal: First-run experience that sells the app and sets context

Build Onboarding/OnboardingView.swift — 4-screen onboarding.

## Screen 1: Bill's Introduction
- Full parchment background (#F5EDD6)
- Centered: large amber candle emoji 🕯️ (large, centered, drop shadow)
- Title (EB Garamond 32pt bold): "My name is Bill W."
- 5 cinematic italic questions above the candle in cascade, muted parchment text:
  "What if Bill W. was still here?"
  "What would you ask him?"
  "How could he help when the urge hits?"
  "When you're between a rock and a hard place?"
  "It's 2am. There's no one else to call."
- Body text (EB Garamond 17pt, SaddleBrown):
  "Bill W. passed away in 1971. But using his complete original writings — the 1939
  Big Book and every public domain word he left behind — we've done our best to bring
  his wisdom back. Ask him anything. It stays between you and Bill."
- CTA: "Meet Bill" — amber pill button, full width
- Tiny footer (mono 10pt, muted):
  "Not a replacement for your sponsor — just someone to talk to at 2am when they can't be there.
   Grounded in Bill W.'s public domain writings (1939). Not affiliated with AAWS."

## Screen 2: "When do you need me most?"
- Header (EB Garamond 26pt): "When do you need me most?"
- Subtitle italic: "Choose all that apply."
- 4 tappable cards (multi-select):
  🌙 "At 3am when I can't sleep"
  ⚡ "When I'm facing a craving"
  📖 "Working through the Steps"
  🤝 "When I need to talk to someone"
- Store selection in AppState.needsSelection: [String]
- CTA: "Continue"

## Screen 3: Sobriety Date (Optional)
- Header (EB Garamond 26pt): "How long have you been on your journey?"
- Subtitle italic: "Optional. This helps Bill be more present with you."
- DatePicker: compact style, max date = today
- "I'd rather not say" link (secondary, small)
- If set: AppState.sobrietyDate = date
- CTA: "Set My Date" (primary) | "Skip for Now" (ghost button)
- Tone: zero judgment. Recovery starts when it starts.

## Screen 4: Free Conversations
- Header (EB Garamond 32pt): "Ask Bill anything."
- Subtitle italic: "Not a replacement for your sponsor or your group — just someone
  to talk to at 2am when they can't be there."
- Free banner card (amber tint): "3 Free Conversations Included — Ask Bill a real question
  right now, no payment needed. See for yourself before committing."
- 3 pricing cards: Weekly $4.99, Monthly $12.99 (MOST POPULAR), Yearly $59.99 (Save 62%)
- CTA (primary): "Start for Free" — amber, full width
- "Restore Purchases" link
- Footer (mono 10pt): "Grounded in Bill W.'s original writings. Not affiliated with AAWS.
  Not a substitute for professional help."
- Tapping CTA: AppState.isOnboardingComplete = true

## Navigation:
- Custom progress dots at top, amber active dot
- No back-swipe on Screen 1
- Swipe to advance is fine for S2-S4

## Test:
- Full flow completes → ContentView shows TabView
- Sobriety date persists to Settings
- Deleting app resets onboarding

git add -A && git commit -m "S4: Onboarding flow, sobriety date, free trial messaging" && git push origin main
```

---

## SESSION 5: Core Chat UI — "Ask Bill" Interface
**Time:** ~90 min | **Test:** 🧪 Test with live API — this is the heart of the app

```
# WWBD iOS — Session 5: Chat UI
# Goal: The Ask Bill conversation screen — must feel like receiving a letter

Build Features/Chat/ChatView.swift, ChatViewModel.swift, BillMessageView.swift,
UserMessageView.swift, MessageInputView.swift, CrisisView.swift.

## ChatView.swift — Layout
NavigationStack {
    VStack(spacing: 0) {
        // Nav bar: "Ask Bill" in EB Garamond, amber 🕯️ icon
        // Free convo counter if not subscribed: "2 conversations remaining" in mono amber

        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 16) {
                    ForEach(viewModel.messages) { message in
                        if message.role == "bill" {
                            BillMessageView(message: message)
                        } else {
                            UserMessageView(message: message)
                        }
                    }
                    if viewModel.isLoading {
                        BillTypingIndicatorView()  // 3 animated amber dots
                    }
                }
                .padding(20)
            }
        }

        MessageInputView(onSend: viewModel.sendMessage)
    }
    .background(Color("ParchmentBackground"))
}

Empty state (no messages yet):
- Centered: 🕯️ large, below it EB Garamond italic: "Ask Bill anything."
  "He's been through it all."
- 4 suggestion chips (tappable, pre-fills input):
  "I'm struggling with a resentment."
  "I'm working on my Step 4."
  "I had a craving come up today."
  "I relapsed. Now what?"

## BillMessageView.swift — Parchment Letter Card
- Background: Color("OldPaper") #EDD9A3
- Border: 1pt Color("AgedGold")
- Border radius: 4pt top-left, 16pt other corners (letter-like, asymmetric)
- Shadow: .shadow(color: .brown.opacity(0.12), radius: 4, y: 2)
- "Bill W." label: mono 10pt, SaddleBrown, uppercased, letter-spaced
- Message body: EB Garamond 17pt, LexiconText (#2C1810), lineSpacing 4
- Citation footer (if citations non-empty):
  - 1pt AgedGold divider
  - "— From [source], [chapter]" in mono 11pt, italic, SaddleBrown
  - SUPPRESS any citation mentioning "Twelve Steps and Twelve Traditions" or "As Bill Sees It"
- Typewriter animation: reveal content character by character, Timer 0.02s interval

## UserMessageView.swift
- Right-aligned bubble
- Background: amber #C8860A at 12% opacity, border: amber 20% opacity
- Border radius: 16pt, top-right corner 4pt
- Text: SF Pro 16pt, LexiconText

## ChatViewModel.swift
@MainActor @Observable class ChatViewModel {
    var messages: [DisplayMessage] = []
    var isLoading = false
    var inputText = ""

    func sendMessage(_ text: String) async {
        // 1. Guard: appState.canSendMessage() else show paywall native sheet
        // 2. Add user message to UI immediately
        // 3. Save to SwiftData
        // 4. Build conversation history from last 6 exchanges (12 messages max)
        // 5. await APIClient.shared.askBill()
        // 6. If crisis == true: present CrisisView as fullScreenCover
        // 7. If normal: add Bill message, start typewriter animation
        // 8. Increment appState.freeConvosUsed
        // 9. Save to SwiftData
    }
}

## CrisisView.swift — Full screen, no dismiss via swipe
- Red/amber gradient background
- Large EB Garamond: "You are not alone."
- 3 tappable resource cards (tap-to-call/text):
  988 Suicide & Crisis Lifeline — Call or text 988
  SAMHSA Helpline — 1-800-662-4357
  Crisis Text Line — Text HOME to 741741
- "Return to Bill" amber button at bottom
- .interactiveDismissDisabled(true)

## MessageInputView.swift
- TextEditor multi-line, parchment bg, AgedGold border, 3pt radius
- Placeholder: "Ask Bill anything..."
- Send button: amber fill, paperplane.fill icon
- Disabled + muted while isLoading
- 500 char limit — show counter when >400

## Native Paywall Sheet (v1 — no Superwall yet):
When canSendMessage() returns false, show a sheet with:
- Title (EB Garamond 28pt): "Bill is waiting for you."
- Subtitle: "Your 3 free conversations are up. A subscription keeps his light on."
- 3 plan cards (same as onboarding screen 4)
- "Begin My Journey" CTA — amber
- "Restore Purchases" link
- This is the hard gate. No "maybe later."

## Test with live API (start uvicorn: uvicorn api.main:app --reload --port 8000):
- Ask "I'm struggling with resentment" — verify Bill response + citation appears
- Send a crisis message — verify CrisisView appears, tap-to-call works
- Use 3 free messages — verify paywall sheet appears on 4th

git add -A && git commit -m "S5: Chat UI, parchment cards, typewriter effect, crisis view, paywall gate" && git push origin main
```

---

## SESSION 6: Daily Reflection Tab + WidgetKit
**Time:** ~60 min | **Test:** Widget preview in Xcode Canvas, API tab working

```
# WWBD iOS — Session 6: Daily Reflection + Widget
# Goal: Tab 2 — daily Bill W. reflection + home screen widget

Build Features/DailyReflection/DailyReflectionView.swift and WhatWouldBillDoWidget extension.

## DailyReflectionView.swift — Tab 2
- Header (EB Garamond 24pt): "Today's Reflection"
- Date: formatted as "Monday, April 20" in mono amber small
- Parchment card (matches BillMessageView style):
  - Passage text: EB Garamond italic 16pt, LexiconText
  - Source citation: mono 11pt, SaddleBrown
- Bill's Reflection section below:
  - "Bill's Reflection" label in amber mono uppercase
  - Reflection text: EB Garamond 15pt
- "Ask Bill about this" CTA → switches to Chat tab with topic pre-filled
- Sobriety counter (if sobrietyDate is set):
  - Large EB Garamond number (days sober)
  - Milestone label: "30 days" / "6 months" / "1 year"
  - Small amber arc decoration

## WidgetKit Extension: WhatWouldBillDoWidget

Create new Widget Extension target: WhatWouldBillDoWidget

Provider:
- Entry: DailyReflectionEntry { date: Date, passage: String, source: String, reflection: String }
- Timeline: one entry refreshed at midnight daily
- Reads from UserDefaults(suiteName: "group.com.whatwouldbilldo.app.shared")

Widget sizes: .systemSmall and .systemMedium

Small widget:
- Parchment background via .containerBackground (REQUIRED — see gotcha below)
- First 80 chars of passage in EB Garamond 12pt
- "— Bill W." in amber mono 10pt
- Tap → deep link to DailyReflectionView

Medium widget:
- Same parchment containerBackground
- First 150 chars of passage + first 60 chars of reflection
- Date top-right in amber mono

## CRITICAL — containerBackground (iOS 17+ required):
Use .containerBackground(for: .widget) { Color("ParchmentBackground") }
NOT .background(). Failure causes wrong/transparent background on iOS 17+.

## App Group for data sharing:
Both main app target AND widget extension target must have:
App Group: group.com.whatwouldbilldo.app.shared
App writes cached reflection to UserDefaults(suiteName: "group.com.whatwouldbilldo.app.shared")
Widget reads from same suite.
Verify both targets have the entitlement in Signing & Capabilities.

## Test:
- Xcode Canvas shows parchment widget with quote
- Tab 2 loads today's reflection from API
- "Ask Bill about this" pre-fills chat with passage topic

git add -A && git commit -m "S6: Daily reflection tab, WidgetKit small/medium, App Group data sharing" && git push origin main
```

---

## SESSION 7: Settings Tab + Subscription Management
**Time:** ~45 min | **Test:** Functional — no special testing needed

```
# WWBD iOS — Session 7: Settings Screen
# Goal: Complete settings tab

Build Features/Settings/SettingsView.swift using List / .insetGrouped style.

## Section: My Journey
- Sobriety Date: DatePicker or "Not set" — tap to edit
- Days Sober: computed from sobrietyDate (large amber number)
- Milestone card (amber glow): appears when days == 1, 7, 30, 60, 90, 180, 365, 730, 1825
  - Hardcode 9 micro-responses from Bill for each milestone

## Section: Subscription
If not subscribed:
  - "X free conversations remaining"
  - "Unlock Bill" button → show native paywall sheet (same as S5)
If subscribed:
  - "✓ Active" in green/teal
  - Plan name + renewal date
  - "Manage Subscription" → URL: itms-apps://apps.apple.com/account/subscriptions
- "Restore Purchases" always visible

## Section: About Bill W.
- Parchment card: "William Griffith Wilson (1895–1971). Co-founder of Alcoholics Anonymous.
  His writings have helped millions find sobriety."
- "View Source Texts" → sheet listing public domain corpus sources

## Section: Legal
- Non-affiliation disclaimer (expandable): This app is not affiliated with AAWS.
- Privacy Policy → open Safari to whatwouldbilldo.com/privacy
- Terms of Service → open Safari to whatwouldbilldo.com/terms
- Send Feedback → mailto:hello@whatwouldbilldo.com

## Section: Developer
- App version (from Bundle)
- API Status → calls checkHealth(), shows "✓ Connected (X passages)" or "⚠ Offline"

## Styling:
- .listStyle(.insetGrouped)
- Section headers: amber mono uppercase
- Consistent with parchment theme but simpler — settings is functional, not cinematic

git add -A && git commit -m "S7: Settings tab, subscription management, sobriety milestones, legal" && git push origin main
```

---

## SESSION 8: Push Notifications + UI Polish
**Time:** ~60 min | **Test:** 🧪 Notifications require real device

```
# WWBD iOS — Session 8: Push Notifications + Polish
# Goal: Daily reflection notification + milestone alerts + full UI polish pass

## Services/NotificationManager.swift
- Request permission after onboarding completes (not on first launch)
- Schedule daily 7:00am notification:
  Title: "Good morning."
  Body: First 60 chars of cached daily reflection passage
  Identifier: "daily_bill_reflection"
  Cancel and reschedule if already scheduled (prevent duplicates)
- Milestone notifications: schedule when sobrietyDate is set/changed
  "30 days. You've done something remarkable."
  "90 days. Bill would want you to know he's proud."
  etc. for each milestone day

## UI Polish Pass:

ChatView:
- Haptic on send: UIImpactFeedbackGenerator(style: .light).impactOccurred()
- Smooth scroll-to-bottom: withAnimation { proxy.scrollTo(lastMessageID) }
- Loading: "Bill is reflecting..." in EB Garamond italic amber, replacing typing indicator
- Ensure input bar doesn't get hidden behind keyboard (.ignoresSafeArea(.keyboard, edges: .bottom) correctly)

BillMessageView:
- Typewriter timer: 0.02s interval, 1 char per tick — ensure it's smooth
- Subtle grain texture overlay: 4% opacity noise pattern on card

General:
- .contentTransition(.numericText()) on days sober counter in Settings
- Dynamic Type: verify all text uses .font(.body) style not hardcoded pt sizes where possible
- VoiceOver: add .accessibilityLabel to all icon buttons and custom views
- All named colors have dark fallback in Assets (even if .light only in v1)

## App Store Review Notes (add as a comment in AppState or README):
"This app is an AI chatbot grounded in Bill W.'s public domain writings (1939 Big Book).
It includes a crisis detection system that immediately redirects to 988 and SAMHSA.
Not affiliated with AAWS. First 3 conversations are free — no test account needed."

## Test on real device:
- Notification arrives at scheduled time
- All 3 tabs working, no crashes
- Full conversation with production API
- Settings: restore purchases, sobriety date, milestones

git add -A && git commit -m "S8: Push notifications, milestone alerts, UI polish, accessibility" && git push origin main
```

---

## SESSION 9: App Icon + TestFlight Upload + Railway Deploy
**Time:** ~60 min | **Test:** 🧪 Full end-to-end on TestFlight before App Review

```
# WWBD iOS — Session 9: Ship to TestFlight
# Goal: Real icon, archive, TestFlight upload, Railway deploy

## App Icon
Create a 1024x1024 app icon:
- Deep amber/brown gradient background (#2C1810 to #8B4513)
- Single centered candle: golden flame (#E8960A), cream body (#F5EDD6), amber holder
- Clean, minimal, recognizable at small sizes
- No text on icon
- Export all required sizes via Asset Catalog

## Pre-flight Checklist:
- Bundle ID matches ASC: com.whatwouldbilldo.app
- Version: 1.0.0, Build: 1
- All 3 IAP product IDs exist in App Store Connect
- API base URL set to production: https://api.whatwouldbilldo.com
- PrivacyInfo.xcprivacy exists in main target (not just widget):
  NSPrivacyTracking = false
  NSPrivacyTrackingDomains = []
  NSPrivacyAccessedAPITypes: NSPrivacyAccessedAPICategoryUserDefaults reason CA92.1
- Signing: Automatic, Team 7BW79QC9WM

## Archive and Upload:
Product → Destination → Any iOS Device (arm64)
Product → Archive
Organizer → Distribute App → App Store Connect → Upload

## Deploy FastAPI to Railway:
1. In the backend repo (whatwouldbilldo, not this iOS repo):
   Create Procfile: web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
2. railway.app → New Project → Deploy from GitHub → ClawdiusMaximus-LIVES/whatwouldbilldo
3. Add env vars: OPENAI_API_KEY, ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY
4. Get Railway URL → add custom domain: api.whatwouldbilldo.com
5. Namecheap DNS: CNAME api → [your-app].up.railway.app

## Verify end-to-end:
curl https://api.whatwouldbilldo.com/health
→ {"status":"ok","passages_count":XXXX}

## TestFlight checklist:
[ ] Onboarding completes without crash
[ ] 3 Bill conversations work (API responding)
[ ] 4th conversation triggers paywall sheet
[ ] All 3 pricing options display
[ ] Sandbox purchase works — paywall dismisses, chat continues
[ ] Daily reflection loads
[ ] Widget appears on home screen
[ ] Notifications arrive at 7am
[ ] Crisis detection redirects to 988 resources
[ ] Settings: sobriety date, milestone, restore purchases

git add -A && git commit -m "S9: App icon, TestFlight upload, Railway deploy, production API" && git push origin main
```

---

# KNOWN GOTCHAS — Read Before Each Session

**Swift 6 Strict Concurrency (S1)**
SWIFT_STRICT_CONCURRENCY = complete. All @Observable classes touching UI must be @MainActor.
ChatViewModel must be @MainActor.

**xcodegen — Regenerate after every new file (S1+)**
Every new .swift file: run xcodegen generate. Add alias: `alias xg='xcodegen generate && open *.xcodeproj'`

**SwiftData @Model — No complex computed properties (S1)**
Store citations as JSON String in Message, not [Citation]. Decode on use.

**StoreKit 2 — No #if DEBUG bypasses (S3)**
Always use .verified(let transaction) pattern. StoreKit .storekit file handles sandbox.

**WidgetKit — containerBackground required for iOS 17+ (S6)**
.containerBackground(for: .widget) { Color("ParchmentBackground") } — not .background()

**App Group on BOTH targets (S6)**
Widget extension AND main app must both have group.com.whatwouldbilldo.app.shared in Signing & Capabilities.

**Superwall configure before first view (S6 — future)**
Call Superwall.configure() in App.init(), not onAppear.

**API timeout (S2, S5)**
Bill responses: 2-8 seconds. URLSession timeout: 30s minimum.
Show "Bill is reflecting..." immediately on send — never leave the UI frozen.

**Conversation history size (S5)**
Send max last 6 exchanges (12 messages) to /ask. Truncate on the iOS side before the call.

**Privacy Manifest required (S9)**
PrivacyInfo.xcprivacy must be in the MAIN TARGET. Apple rejects without it.
NSPrivacyAccessedAPICategoryUserDefaults with reason CA92.1.

**Copyright — never display Twelve & Twelve or As Bill Sees It (All sessions)**
If API citation contains either title, suppress it silently in the UI. Do not show the user.

**Force light mode (S1)**
.preferredColorScheme(.light) on root WindowGroup content. Dark mode is v1.1.

document.addEventListener("DOMContentLoaded", () => {
    // ── STATE VARIABLES ──
    let activeRound = null;
    let currentUser = null;
    let activeHandIndex = 0; // Tracks which split hand the player is currently operating on

    // ── DOM ELEMENTS ──
    const authPanel = document.getElementById("auth-panel");
    const gamePanel = document.getElementById("game-panel");
    const authForm = document.getElementById("auth-form");
    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const emailGroup = document.getElementById("email-group");
    const authSubmitBtn = document.getElementById("auth-submit-btn");
    const authError = document.getElementById("auth-error");
    
    const usernameInput = document.getElementById("username");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");

    const headerUsername = document.getElementById("header-username");
    const chipsCounter = document.getElementById("chips-counter");
    const logoutBtn = document.getElementById("logout-btn");

    const dealerCards = document.getElementById("dealer-cards");
    const dealerScoreBadge = document.getElementById("dealer-score-badge");
    const playerHandsContainer = document.getElementById("player-hands-container");
    
    const outcomeOverlay = document.getElementById("outcome-overlay");
    const outcomeText = document.getElementById("outcome-text");

    const bettingControls = document.getElementById("betting-controls");
    const actionControls = document.getElementById("action-controls");
    const betAmountInput = document.getElementById("bet-amount");
    const dealBtn = document.getElementById("deal-btn");

    const hitBtn = document.getElementById("hit-btn");
    const standBtn = document.getElementById("stand-btn");
    const doubleBtn = document.getElementById("double-btn");
    const splitBtn = document.getElementById("split-btn");
    const insuranceBtn = document.getElementById("insurance-btn");

    const statTotal = document.getElementById("stat-total");
    const statRate = document.getElementById("stat-rate");
    const statWlp = document.getElementById("stat-wlp");
    const statNet = document.getElementById("stat-net");

    // ── INITIAL BINDINGS / AUTH FLOW ──
    
    // Toggle Login/Register Tabs
    tabLogin.addEventListener("click", () => {
        tabLogin.classList.add("active");
        tabRegister.classList.remove("active");
        emailGroup.classList.add("hidden");
        emailInput.removeAttribute("required");
        authSubmitBtn.textContent = "Login";
        authError.textContent = "";
    });

    tabRegister.addEventListener("click", () => {
        tabRegister.classList.add("active");
        tabLogin.classList.remove("active");
        emailGroup.classList.remove("hidden");
        emailInput.setAttribute("required", "true");
        authSubmitBtn.textContent = "Register";
        authError.textContent = "";
    });

    // Form Submission
    authForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        authError.textContent = "";

        const isLogin = tabLogin.classList.contains("active");
        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        try {
            if (isLogin) {
                await BlackjackAPI.login(username, password);
            } else {
                const email = emailInput.value.trim();
                await BlackjackAPI.register(username, email, password);
                // Auto-login after register
                await BlackjackAPI.login(username, password);
            }
            initSession();
        } catch (err) {
            authError.textContent = err.message || "Authentication failed.";
        }
    });

    // Logout Action
    logoutBtn.addEventListener("click", () => {
        BlackjackAPI.logout();
        showAuthScreen();
    });

    // Handle token expiration events
    window.addEventListener("auth_expired", () => {
        showAuthScreen();
    });

    // ── BETTING & CHIP SELECTION ──
    
    // Chip Buttons
    document.querySelectorAll(".chip-btn").forEach(chip => {
        chip.addEventListener("click", () => {
            const val = parseInt(chip.getAttribute("data-value"));
            const currentBet = parseInt(betAmountInput.value) || 0;
            betAmountInput.value = currentBet + val;
        });
    });

    // Start Round Deal button
    dealBtn.addEventListener("click", async () => {
        const bet = parseInt(betAmountInput.value);
        if (isNaN(bet) || bet < 10) {
            alert("Minimum bet is 10 chips.");
            return;
        }

        try {
            outcomeOverlay.classList.add("hidden");
            const roundData = await BlackjackAPI.startRound(bet);
            updateGameState(roundData);
        } catch (err) {
            alert(err.message);
        }
    });

    // ── GAME PLAY ACTIONS ──

    hitBtn.addEventListener("click", () => sendAction("hit"));
    standBtn.addEventListener("click", () => sendAction("stand"));
    doubleBtn.addEventListener("click", () => sendAction("double"));
    splitBtn.addEventListener("click", () => sendAction("split"));
    insuranceBtn.addEventListener("click", () => sendAction("insurance"));

    async function sendAction(actionType) {
        try {
            const roundData = await BlackjackAPI.playAction(actionType, activeHandIndex);
            updateGameState(roundData);
        } catch (err) {
            alert(err.message);
        }
    }

    // ── GAME ENGINE RENDERING ──

    function getSuitSymbol(suitCode) {
        switch (suitCode) {
            case "H": return "♥";
            case "D": return "♦";
            case "C": return "♣";
            case "S": return "♠";
            default: return "";
        }
    }

    function getSuitClass(suitCode) {
        return (suitCode === "H" || suitCode === "D") ? "red-suit" : "black-suit";
    }

    // Helper to generate playing card DOM element
    function createCardElement(card, index, isHidden = false) {
        const el = document.createElement("div");
        el.className = `playing-card ${isHidden ? 'card-back' : getSuitClass(card.suit)}`;
        el.style.left = `${index * 20}px`;
        el.style.zIndex = index + 1;
        
        // CSS animations
        el.style.transform = "translateY(-50px) rotate(-10deg)";
        el.style.opacity = "0";

        setTimeout(() => {
            el.style.transform = "none";
            el.style.opacity = "1";
        }, index * 150);

        if (isHidden) {
            el.innerHTML = `
                <div class="card-back-pattern">
                    <span>👑</span>
                </div>
            `;
        } else {
            const sym = getSuitSymbol(card.suit);
            el.innerHTML = `
                <div class="card-top">
                    <span class="card-value-label">${card.value}</span>
                    <span class="card-suit-label">${sym}</span>
                </div>
                <div class="card-center-suit">${sym}</div>
                <div class="card-bottom">
                    <span class="card-value-label">${card.value}</span>
                    <span class="card-suit-label">${sym}</span>
                </div>
            `;
        }
        return el;
    }

    function renderDealer(dealerHand, status) {
        dealerCards.innerHTML = "";
        
        const cards = dealerHand.cards;
        const score = dealerHand.value;

        // If playing, dealer's second card is face down (hidden)
        const hideHoleCard = (status === "playing");

        cards.forEach((card, idx) => {
            const isHole = hideHoleCard && idx === 1;
            dealerCards.appendChild(createCardElement(card, idx, isHole));
        });

        // Score display adjustments
        if (hideHoleCard) {
            dealerScoreBadge.classList.remove("hidden");
            // Show only first card value
            const firstCardVal = getFirstCardDisplayValue(cards[0]);
            dealerScoreBadge.textContent = firstCardVal.toString();
        } else {
            dealerScoreBadge.classList.remove("hidden");
            dealerScoreBadge.textContent = score.toString();
        }
    }

    function getFirstCardDisplayValue(card) {
        if (["J", "Q", "K"].includes(card.value)) return 10;
        if (card.value === "A") return 11;
        return parseInt(card.value);
    }

    function renderPlayer(playerHands) {
        playerHandsContainer.innerHTML = "";

        playerHands.forEach((hand, idx) => {
            const handBox = document.createElement("div");
            handBox.className = "player-hand-box";
            
            // Highlight hand currently playing (for splits)
            if (playerHands.length > 1 && hand.status === "playing" && idx === activeHandIndex) {
                handBox.classList.add("active-hand");
            } else if (playerHands.length === 1 && hand.status === "playing") {
                handBox.classList.add("active-hand");
            }

            // Cards wrapper
            const cardsSlot = document.createElement("div");
            cardsSlot.className = "cards-slot";
            hand.cards.forEach((card, cardIdx) => {
                cardsSlot.appendChild(createCardElement(card, cardIdx));
            });

            // Hand metadata overlay labels
            const labelRow = document.createElement("div");
            labelRow.className = "section-label";
            labelRow.innerHTML = `
                HAND ${playerHands.length > 1 ? (idx + 1) : ""} 
                <span class="score-badge">${hand.value}</span>
            `;

            const infoRow = document.createElement("div");
            infoRow.className = "hand-info-row";
            infoRow.innerHTML = `Bet: 💰${hand.bet} | <span class="hand-status">${hand.status.toUpperCase()}</span>`;

            handBox.appendChild(labelRow);
            handBox.appendChild(cardsSlot);
            handBox.appendChild(infoRow);
            
            playerHandsContainer.appendChild(handBox);
        });
    }

    // ── GAME STATE COORDINATOR ──

    function updateGameState(round) {
        activeRound = round;
        
        // Auto-select the first playing hand
        activeHandIndex = round.player_hands.findIndex(h => h.status === "playing");
        if (activeHandIndex === -1) {
            activeHandIndex = 0; // Fallback to first
        }

        renderDealer(round.dealer_hand, round.status);
        renderPlayer(round.player_hands);

        if (round.status === "playing") {
            // Hide bet inputs, show actions
            bettingControls.classList.add("hidden");
            actionControls.classList.remove("hidden");

            // Evaluate conditional actions
            const currentHand = round.player_hands[activeHandIndex];
            
            // 1. Double action: Only on starting deal (2 cards)
            if (currentHand.cards.length === 2) {
                doubleBtn.classList.remove("hidden");
            } else {
                doubleBtn.classList.add("hidden");
            }

            // 2. Split action: Exactly 2 cards matching value
            const isPair = currentHand.cards.length === 2 && 
                           (getFirstCardDisplayValue(currentHand.cards[0]) === getFirstCardDisplayValue(currentHand.cards[1]));
            if (isPair && round.player_hands.length < 4) { // typical house limit 4 splits max
                splitBtn.classList.remove("hidden");
            } else {
                splitBtn.classList.add("hidden");
            }

            // 3. Insurance action: Dealer showing Ace, first action
            const isDealerAce = round.dealer_hand.cards[0].value === "A";
            const noActionsPlayed = round.actions.length === 0;
            if (isDealerAce && noActionsPlayed && round.insurance_bet === null) {
                insuranceBtn.classList.remove("hidden");
            } else {
                insuranceBtn.classList.add("hidden");
            }

        } else {
            // Round complete
            bettingControls.classList.remove("hidden");
            actionControls.classList.add("hidden");
            
            // Display outcome overlay
            displayRoundOutcome(round);
            
            // Refresh chip displays and stats
            refreshStats();
        }
    }

    function displayRoundOutcome(round) {
        outcomeOverlay.classList.remove("hidden");
        
        // Formatting outcomes beautifully
        let bannerText = "";
        const outcome = round.outcome;

        if (outcome === "player_won") {
            bannerText = "🏆 PLAYER WINS!";
        } else if (outcome === "player_lost") {
            bannerText = "💀 DEALER WINS";
        } else if (outcome === "player_push") {
            bannerText = "⚖️ PUSH (TIE)";
        } else if (outcome === "player_blackjack") {
            bannerText = "💥 BLACKJACK ROYAL!";
        } else if (outcome === "split_mixed") {
            bannerText = "⚖️ MIXED OUTCOMES";
        } else {
            bannerText = "ROUND FINISHED";
        }

        const net = round.payout - round.bet - (round.insurance_bet || 0);
        if (net > 0) {
            bannerText += ` (+$${net})`;
            outcomeText.style.color = "var(--gold)";
        } else if (net < 0) {
            bannerText += ` (-$${Math.abs(net)})`;
            outcomeText.style.color = "var(--danger)";
        } else {
            bannerText += ` (Push)`;
            outcomeText.style.color = "var(--text-light)";
        }

        outcomeText.textContent = bannerText;
    }

    // ── PROFILE & STATS LOADING ──

    async function initSession() {
        try {
            currentUser = await BlackjackAPI.getMe();
            headerUsername.textContent = currentUser.username;
            chipsCounter.textContent = currentUser.chips_balance.toString();
            
            // Transition view panels
            authPanel.classList.add("hidden");
            gamePanel.classList.remove("hidden");

            refreshStats();
        } catch (err) {
            showAuthScreen();
        }
    }

    async function refreshStats() {
        try {
            const stats = await BlackjackAPI.getStats();
            
            // Refresh user details (chips balance updates)
            chipsCounter.textContent = stats.chips_balance.toString();

            // Set dashboard stats values
            statTotal.textContent = stats.total_rounds.toString();
            statRate.textContent = `${stats.win_rate}%`;
            statWlp.textContent = `${stats.wins} / ${stats.losses} / ${stats.pushes}`;
            
            const net = stats.net_payout;
            statNet.textContent = (net >= 0 ? "+" : "") + net.toString();
            
            statNet.className = "stat-value";
            if (net > 0) {
                statNet.classList.add("profit-positive");
            } else if (net < 0) {
                statNet.classList.add("profit-negative");
            } else {
                statNet.classList.add("profit-neutral");
            }
        } catch (err) {
            console.error("Failed to load statistics dashboard", err);
        }
    }

    function showAuthScreen() {
        authPanel.classList.remove("hidden");
        gamePanel.classList.add("hidden");
        authForm.reset();
        activeRound = null;
        currentUser = null;
    }

    // Auto-check auth state at launch
    if (BlackjackAPI.isAuthenticated()) {
        initSession();
    } else {
        showAuthScreen();
    }
});

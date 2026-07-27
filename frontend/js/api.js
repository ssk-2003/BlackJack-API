const API_BASE_URL = window.location.origin + "/api";

class BlackjackAPI {
    static getHeaders() {
        const headers = {
            "Content-Type": "application/json"
        };
        const token = localStorage.getItem("access_token");
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        return headers;
    }

    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        options.headers = {
            ...this.getHeaders(),
            ...options.headers
        };

        try {
            const response = await fetch(url, options);
            
            if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem("access_token");
                window.dispatchEvent(new Event("auth_expired"));
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error on ${endpoint}:`, error);
            throw error;
        }
    }

    static async register(username, email, password) {
        return this.request("/auth/register", {
            method: "POST",
            body: JSON.stringify({ username, email, password })
        });
    }

    static async login(username, password) {
        const data = await this.request("/auth/login", {
            method: "POST",
            body: JSON.stringify({ username, password })
        });
        if (data.access_token) {
            localStorage.setItem("access_token", data.access_token);
        }
        return data;
    }

    static async getMe() {
        return this.request("/auth/me");
    }

    static async getStats() {
        return this.request("/stats/me");
    }

    static async startRound(bet) {
        return this.request("/game/start", {
            method: "POST",
            body: JSON.stringify({ bet })
        });
    }

    static async playAction(actionType, handIndex = 0) {
        return this.request("/game/action", {
            method: "POST",
            body: JSON.stringify({ action_type: actionType, hand_index: handIndex })
        });
    }

    static async getHistory() {
        return this.request("/game/history");
    }

    static logout() {
        localStorage.removeItem("access_token");
    }

    static isAuthenticated() {
        return !!localStorage.getItem("access_token");
    }
}

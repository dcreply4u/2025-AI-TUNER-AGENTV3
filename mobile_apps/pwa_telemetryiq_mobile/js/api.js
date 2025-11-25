// TelemetryIQ Mobile API Service
// Matches desktop API endpoints

class TelemetryIQAPI {
    constructor(baseUrl = 'http://192.168.1.100:8000') {
        this.baseUrl = baseUrl;
    }

    async getCurrentTelemetry(sensors = null) {
        try {
            let url = `${this.baseUrl}/api/telemetry/current`;
            if (sensors && sensors.length > 0) {
                url += `?sensors=${sensors.join(',')}`;
            }
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching telemetry:', error);
            throw error;
        }
    }

    async getSensors() {
        try {
            const response = await fetch(`${this.baseUrl}/api/telemetry/sensors`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            return data.sensors || [];
        } catch (error) {
            console.error('Error fetching sensors:', error);
            throw error;
        }
    }

    async applyConfigChange(changeType, category, parameter, newValue, oldValue = null) {
        try {
            const response = await fetch(`${this.baseUrl}/api/config/change`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    change_type: changeType,
                    category: category,
                    parameter: parameter,
                    new_value: newValue,
                    old_value: oldValue,
                }),
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error applying config change:', error);
            throw error;
        }
    }

    async askAIAdvisor(question, context = {}) {
        try {
            const response = await fetch(`${this.baseUrl}/api/ai/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    context: context,
                }),
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error asking AI advisor:', error);
            throw error;
        }
    }

    async getConfigHistory(category = null, limit = 50) {
        try {
            let url = `${this.baseUrl}/api/config/history?limit=${limit}`;
            if (category) {
                url += `&category=${encodeURIComponent(category)}`;
            }
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            return data.changes || [];
        } catch (error) {
            console.error('Error fetching config history:', error);
            throw error;
        }
    }

    async getSystemStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/api/system/status`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error getting system status:', error);
            throw error;
        }
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TelemetryIQAPI;
}

















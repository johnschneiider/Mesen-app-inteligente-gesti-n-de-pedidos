/**
 * orders_ws.js — WebSocket client para pedidos en vivo
 * Se conecta al canal del negocio y actualiza la UI en tiempo real.
 */
class OrdersWebSocket {
    constructor(onUpdate) {
        this.onUpdate = onUpdate;
        this.reconnectDelay = 3000;
        this.connect();
    }

    connect() {
        const proto = location.protocol === 'https:' ? 'wss' : 'ws';
        this.ws = new WebSocket(`${proto}://${location.host}/ws/orders/`);

        this.ws.onopen = () => {
            console.log('[WS] Conectado a pedidos en vivo');
        };

        this.ws.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                this.onUpdate(data);
            } catch (err) {
                console.error('[WS] Error parseando mensaje:', err);
            }
        };

        this.ws.onclose = (e) => {
            console.log(`[WS] Desconectado (code=${e.code}). Reconectando en ${this.reconnectDelay}ms…`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        };

        this.ws.onerror = (err) => {
            console.error('[WS] Error:', err);
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.onclose = null; // prevent reconnect
            this.ws.close();
        }
    }
}

/**
 * Inicializa el panel de pedidos en vivo.
 * Busca el contenedor #live-orders-container y maneja los eventos.
 */
function initLiveOrders() {
    const container = document.getElementById('live-orders-container');
    const counter = document.getElementById('pending-counter');
    if (!container) return;

    const ws = new OrdersWebSocket((data) => {
        if (data.event === 'new_order') {
            showNewOrderNotification(data);
            // HTMX reload del contenedor de pedidos
            htmx.trigger(container, 'orderUpdate');
            // update counter badge
            if (counter) {
                const current = parseInt(counter.textContent || '0', 10);
                counter.textContent = current + 1;
                counter.style.display = 'flex';
            }
        } else if (data.event === 'status_change') {
            // Actualizar la fila del pedido específico vía HTMX
            const row = document.getElementById(`order-row-${data.order_id}`);
            if (row) {
                htmx.trigger(row, 'statusChange');
            }
            htmx.trigger(container, 'orderUpdate');
        }
    });

    // Cleanup al salir de la página
    window.addEventListener('beforeunload', () => ws.disconnect());
}

function showNewOrderNotification(data) {
    // Notificación toast sencilla
    const toast = document.createElement('div');
    toast.className = 'ws-toast';
    toast.innerHTML = `
        <strong>Nuevo pedido #${data.order_number}</strong>
        <span>${data.client} · ${data.menu} ×${data.quantity}</span>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

// Auto-inicializar
document.addEventListener('DOMContentLoaded', initLiveOrders);

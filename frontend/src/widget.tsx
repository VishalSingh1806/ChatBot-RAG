// Widget initialization script for embedding on external websites
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Global namespace for the widget
declare global {
  interface Window {
    ReCircleChatbot: {
      init: (config?: WidgetConfig) => void;
      destroy: () => void;
    };
  }
}

interface WidgetConfig {
  position?: 'bottom-right' | 'bottom-left';
  // Add more config options as needed
}

let widgetRoot: ReactDOM.Root | null = null;
let widgetContainer: HTMLDivElement | null = null;

const ReCircleChatbot = {
  init: (config: WidgetConfig = {}) => {
    // Prevent multiple initializations
    if (widgetContainer) {
      console.warn('ReCircle Chatbot is already initialized');
      return;
    }

    // Create container div for the widget
    widgetContainer = document.createElement('div');
    widgetContainer.id = 'recircle-chatbot-widget';
    widgetContainer.style.cssText = `
      position: fixed;
      bottom: 0;
      right: 0;
      z-index: 999999;
      width: 100%;
      height: 100%;
      pointer-events: none;
    `;

    // Allow clicks on chat elements
    widgetContainer.addEventListener('click', (e) => {
      e.stopPropagation();
    });

    document.body.appendChild(widgetContainer);

    // Create a React root and render the app
    widgetRoot = ReactDOM.createRoot(widgetContainer);
    widgetRoot.render(
      <React.StrictMode>
        <div style={{ pointerEvents: 'auto' }}>
          <App />
        </div>
      </React.StrictMode>
    );

    console.log('✅ ReCircle Chatbot initialized');
  },

  destroy: () => {
    if (widgetRoot) {
      widgetRoot.unmount();
      widgetRoot = null;
    }
    if (widgetContainer) {
      document.body.removeChild(widgetContainer);
      widgetContainer = null;
    }
    console.log('🗑️ ReCircle Chatbot destroyed');
  }
};

// Expose the widget API globally
window.ReCircleChatbot = ReCircleChatbot;

// Auto-initialize if data attribute is present
if (document.currentScript?.hasAttribute('data-auto-init')) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      ReCircleChatbot.init();
    });
  } else {
    ReCircleChatbot.init();
  }
}

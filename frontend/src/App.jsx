import { useState } from 'react';
import Layout from './components/layout/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import { NotificationProvider } from './contexts/NotificationContext';
import NotificationContainer from './components/NotificationContainer';
import Chatbot from './views/Chatbot';
import Dashboard from './views/Dashboard';
import Demos from './views/Demos';
import AdminSettings from './views/AdminSettings';
import Advanced from './views/Advanced';
import About from './views/About';
import './styles/global.css';

const VIEWS = {
  chatbot: Chatbot,
  dashboard: Dashboard,
  demos: Demos,
  admin: AdminSettings,
  advanced: Advanced,
  about: About
};

export default function App() {
  const [currentView, setCurrentView] = useState('chatbot');
  
  const CurrentViewComponent = VIEWS[currentView] || Chatbot;
  
  return (
    <ErrorBoundary>
      <NotificationProvider>
        <Layout currentView={currentView} onViewChange={setCurrentView}>
          <ErrorBoundary key={currentView}>
            <CurrentViewComponent />
          </ErrorBoundary>
        </Layout>
        <NotificationContainer />
      </NotificationProvider>
    </ErrorBoundary>
  );
}
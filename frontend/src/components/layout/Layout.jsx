import Sidebar from './Sidebar';
import './Layout.css';

export default function Layout({ currentView, onViewChange, children }) {
  return (
    <div className="app-container">
      <Sidebar currentView={currentView} onViewChange={onViewChange} />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
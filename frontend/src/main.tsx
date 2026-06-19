import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

console.log('--- REBOOTING MAIN.TSX ---');

const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(<App />);
  console.log('--- RENDER CALLED ---');
} else {
  console.log('--- NO ROOT FOUND ---');
}

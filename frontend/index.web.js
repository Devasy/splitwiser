import { createRoot } from 'react-dom/client';
import { AppRegistry } from 'react-native';
import App from './App';

const rootTag = document.getElementById('root');
const root = createRoot(rootTag);

AppRegistry.registerComponent('main', () => App);
root.render(<App />);

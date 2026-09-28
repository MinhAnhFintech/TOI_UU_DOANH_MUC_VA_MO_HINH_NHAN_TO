import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import DataPage from './pages/DataPage';
import FactorsPage from './pages/FactorsPage';
import RegressionPage from './pages/RegressionPage';
import ModelsPage from './pages/ModelsPage';
import QuantilePage from './pages/QuantilePage';
import FrontierPage from './pages/FrontierPage';
import WeightsPage from './pages/WeightsPage';
import BacktestPage from './pages/BacktestPage';
import SensitivityPage from './pages/SensitivityPage';
import ConclusionPage from './pages/ConclusionPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/data" replace />} />
        <Route path="data" element={<DataPage />} />
        <Route path="factors" element={<FactorsPage />} />
        <Route path="regression" element={<RegressionPage />} />
        <Route path="models" element={<ModelsPage />} />
        <Route path="quantile" element={<QuantilePage />} />
        <Route path="frontier" element={<FrontierPage />} />
        <Route path="weights" element={<WeightsPage />} />
        <Route path="backtest" element={<BacktestPage />} />
        <Route path="sensitivity" element={<SensitivityPage />} />
        <Route path="conclusion" element={<ConclusionPage />} />
      </Route>
    </Routes>
  );
}

import Container from 'react-bootstrap/Container';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import FlashProvider from './contexts/FlashProvider';
import ApiProvider from './contexts/ApiProvider';
import UserProvider from './contexts/UserProvider';
import Header from './components/Header';
import PublicRoute from './components/PublicRoute';
import PrivateRoute from './components/PrivateRoute';
import WelcomePage from './pages/WelcomePage';
//import ExplorePage from './pages/ExplorePage';
//import UserPage from './pages/UserPage';
//import EditUserPage from './pages/EditUserPage';
//import ChangePasswordPage from './pages/ChangePasswordPage';
import LoginPage from './pages/LoginPage';
import RegistrationPage from './pages/RegistrationPage';
//import ResetRequestPage from './pages/ResetRequestPage';
//import ResetPage from './pages/ResetPage';

export default function App() {
  return (
    <Container fluid className="App">
      <BrowserRouter>
        <FlashProvider>
          <ApiProvider>
            <UserProvider>
              <Header />
              <Routes>
                <Route path="/web-user-login" element={
                  <PublicRoute><LoginPage /></PublicRoute>
                } />
                <Route path="/web-user-register" element={
                  <PublicRoute><RegistrationPage /></PublicRoute>
                } />
                <Route path="*" element={
                  <PrivateRoute>
                    <Routes>
                      <Route path="/" element={<WelcomePage />} />
                      <Route path="*" element={<Navigate to="/" />} />
                    </Routes>
                  </PrivateRoute>
                } />
              </Routes>
            </UserProvider>
          </ApiProvider>
        </FlashProvider>
      </BrowserRouter>
    </Container>
  );
}

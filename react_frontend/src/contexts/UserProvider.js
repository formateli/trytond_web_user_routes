import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useApi } from './ApiProvider';

const TRYTON_SERVER = process.env.REACT_APP_TRYTON_SERVER;
const TRYTON_DATABASE = process.env.REACT_APP_TRYTON_DATABASE;

const UserContext = createContext();

export default function UserProvider({ children }) {
  const [user, setUser] = useState();
  const api = useApi();

  useEffect(() => {
    (async () => {
      if (api.isAuthenticated()) {
        const response = await api.get(TRYTON_SERVER, TRYTON_DATABASE, '/web-user-me');
        setUser(response.ok ? response.body : null);
      }
      else {
        setUser(null);
      }
    })();
  }, [api]);

  const login = useCallback(async (username, password, server, database) => {
    const result = await api.login(username, password, server, database);
    console.log(result)
    if (result === 'ok') {
      const response = await api.get(server, database, '/web-user-me');
      setUser(response.ok ? response.body : null);
    }
    return result;
  }, [api]);

  const logout = useCallback(async () => {
    await api.logout(TRYTON_SERVER, TRYTON_DATABASE);
    setUser(null);
  }, [api]);

  return (
    <UserContext.Provider value={{ user, setUser, login, logout }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}

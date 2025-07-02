import Body from '../components/Body';
import { useUser } from '../contexts/UserProvider';

export default function WelcomePage() {
const { user } = useUser();

  return (
    <Body sidebar>
      <h1>Welcome {user.name}</h1>
    </Body>
  ); 
}


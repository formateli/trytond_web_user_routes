import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Body from '../components/Body';
import InputField from '../components/InputField';
import { useApi } from '../contexts/ApiProvider';
import { useFlash } from '../contexts/FlashProvider';

const TRYTON_SERVER = process.env.REACT_APP_TRYTON_SERVER;
const TRYTON_DATABASE = process.env.REACT_APP_TRYTON_DATABASE;

export default function RegistrationPage() {
  const [formErrors, setFormErrors] = useState({});
  const nameField = useRef();
  const emailField = useRef();
  const stayField = useRef();
  const passwordField = useRef();
  const password2Field = useRef();
  const navigate = useNavigate();
  const api = useApi();
  const flash = useFlash();
  //const server = TRYTON_SERVER + '/' + TRYTON_DATABASE

  useEffect(() => {
    nameField.current.focus();
  }, []);

  const onSubmit = async (event) => {
    event.preventDefault();
    const name = nameField.current.value;
    const username = emailField.current.value;
    const stay = stayField.current.checked;
    const password = passwordField.current.value;
    const password2 = password2Field.current.value;

    const errors = {};
    if (!name) {
      errors.name = 'Name must not be empty.';
    }
    if (!username) {
      errors.username = 'Email must not be empty.';
    }
    if (!password) {
      errors.password = 'Password must not be empty.';
    }
    if (!password2) {
      errors.password2 = 'Password2 must not be empty.';
    }
    if (password !== password2) {
      errors.password2 = "Passwords don't match.";
    }
    setFormErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    const data = await api.post(TRYTON_SERVER, TRYTON_DATABASE, '/web-user-register', {
      name: name,
      username: username,
      password: password,
      stay_logged_in: stay
    });

    setFormErrors({});
    if (!data.ok) {
      flash(data.body, 'danger');
    }
    else {
      flash('You have successfully registered!', 'success');
      navigate('/web-user-login');
    }
  };

  return (
    <Body>
      <h1>Register</h1>
      <Form onSubmit={onSubmit}>
        <InputField
          name="name" label="Name"
          error={formErrors.name} fieldRef={nameField} />
        <InputField
          name="email" label="Email address"
          error={formErrors.username} fieldRef={emailField} />
        <InputField
          name="password" label="Password" type="password"
          error={formErrors.password} fieldRef={passwordField} />
        <InputField
          name="password2" label="Password again" type="password"
          error={formErrors.password2} fieldRef={password2Field} />
        <InputField
          name="stay" label="Stay logged in" type="switch"
          error={formErrors.stay} fieldRef={stayField} />
        <Button variant="primary" type="submit">Register</Button>
      </Form>
    </Body>
  );
}

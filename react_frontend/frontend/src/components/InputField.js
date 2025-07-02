import Form from 'react-bootstrap/Form';

export default function InputField(
  { name, label, type, placeholder, error, fieldRef }
) {
  return (
    <Form.Group controlId={name} className="inputField">
      {label && <Form.Label>{label}</Form.Label>}
 
      {type === 'checkbox' || type === 'switch' ? 
        <Form.Check
          type={type}
          placeholder={placeholder}
          ref={fieldRef}
	  inline="true"
	  className="CheckField"
	/> :
        <Form.Control
          type={type || 'text'}
          placeholder={placeholder}
          ref={fieldRef}
	/>
      }

      <Form.Text className="text-danger">{error}</Form.Text>
    </Form.Group>
  );
}

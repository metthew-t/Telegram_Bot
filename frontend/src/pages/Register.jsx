import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { register, login } from '../api.js';
import { saveAuth } from '../auth.js';

export default function RegisterPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    try {
      await register({ username, email, password, role: 'admin' });
      const data = await login({ username, password });
      saveAuth(data);
      onLogin(data.user);
      navigate('/');
    } catch (err) {
      if (err.response?.data) {
        const data = err.response.data;
        const msg = data.detail || data.error ||
          (data.username ? `Username: ${data.username[0]}` : null) ||
          (data.password ? `Password: ${data.password[0]}` : null) ||
          (data.email ? `Email: ${data.email[0]}` : null) ||
          (data.role ? `Role: ${data.role[0]}` : null) ||
          'Unable to register.';
        setError(msg);
      } else {
        setError('Connection error. Is the backend running?');
      }
    }
  };

  return (
    <section className="page-panel">
      <div className="panel-header">
        <h1>Support Staff Registration</h1>
        <p>Create an account to join the support team and manage cases.</p>
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} required />
        </label>

        <label>
          Email
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>

        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} />
        </label>

        {error && <div className="form-error">{error}</div>}

        <button className="button button-primary" type="submit">
          Register
        </button>
      </form>
    </section>
  );
}

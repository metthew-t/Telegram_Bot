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
      await register({ username, email, password });
      const data = await login({ username, password });
      saveAuth(data);
      onLogin(data.user);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.username?.[0] || 'Unable to register.');
    }
  };

  return (
    <section className="page-panel">
      <div className="panel-header">
        <h1>Create an account</h1>
        <p>Register now and manage your cases from one place.</p>
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

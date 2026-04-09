import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api.js';
import { saveAuth } from '../auth.js';

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      const data = await login({ username, password });
      saveAuth(data);
      onLogin(data.user);

      if (data.user.role === 'owner') {
        navigate('/owner');
      } else if (data.user.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Unable to login.');
    }
  };

  return (
    <section className="page-panel">
      <div className="panel-header">
        <h1>Welcome back</h1>
        <p>Use your credentials to access the support dashboard.</p>
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} required />
        </label>

        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>

        {error && <div className="form-error">{error}</div>}

        <button className="button button-primary" type="submit">
          Login
        </button>
      </form>
    </section>
  );
}

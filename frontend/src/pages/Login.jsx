import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import dxcIcon from '../assets/dxc.png';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),  // Ensure the payload is a JSON string
      });

      if (response.ok) {
        navigate('/chat');
      } else {
        const data = await response.json();
        setErrorMessage(data.error || 'Login failed');
      }
    } catch (error) {
      console.error('Error:', error);
      setErrorMessage('An error occurred');
    }
  };

  const handleClick = () => {
    navigate('/Register'); // Change '/upload' to your actual upload page route
};

  return (
    <div className="w-screen h-screen flex justify-center bg-[#f0f4f9]">
      <div className="max-w-sm mx-auto">
        <div className="flex justify-center mb-2 w-[400px]">
          <img src={dxcIcon} alt="DXC Logo" className="my-5 h-50 w-50" />
        </div>
        <form onSubmit={handleLogin}>
          <div className="mb-5">
            <label htmlFor="username" className="block mb-2 text-sm font-medium text-gray-900">
              Username
            </label>
            <input
              type="text"
              id="username"
              className="shadow-sm bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="mb-5">
            <label htmlFor="password" className="block mb-2 text-sm font-medium text-gray-900">
             Password
            </label>
            <input
              type="password"
              id="password"
              placeholder="Password"
              className="shadow-sm bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="flex justify-between">
            <button
              type="submit"
              className="w-full mr-2 text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center"
            >
              Login
            </button>
          </div>
          <p className='my-2'>Don't have an account? <button  className="text-blue-700 font-bold" onClick={handleClick}>Sign up</button></p>
        </form>
        {errorMessage && <p className="text-red-500 mt-2">{errorMessage}</p>}
      </div>
    </div>
  );
}

export default Login;

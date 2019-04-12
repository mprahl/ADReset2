import React, { Component } from 'react';

import AuthService from '../utils/AuthService';

class Home extends Component {
  constructor(props) {
    super(props);
    this.authService = new AuthService();
  }

  render() {
    return <div>Home</div>;
  }
}
export default Home;

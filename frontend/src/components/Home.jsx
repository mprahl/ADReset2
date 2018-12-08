import React, { Component } from 'react';
import { PropTypes } from 'prop-types';

import SetQuestion from './SetQuestion';
import AuthService from './AuthService';


class Home extends Component {
  static propTypes = {
    displayToast: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props);
    this.authService = new AuthService();
  }

  render() {
    if (this.authService.isAdmin()) {
      return (
        <SetQuestion displayToast={this.props.displayToast} />
      );
    }

    return (
      <div>Home</div>
    );
  }
}
export default Home;

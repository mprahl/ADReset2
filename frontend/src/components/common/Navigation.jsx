import React, { Component } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { PropTypes } from 'prop-types';
import {
  Container,
  Collapse,
  Navbar,
  NavbarToggler,
  NavbarBrand,
  Nav,
  NavItem,
  NavLink,
} from 'reactstrap';

import AuthService from '../../utils/AuthService';
import './Navigation.css';
import logo from '../../imgs/logo.png';

class Navigation extends Component {
  static propTypes = {
    history: PropTypes.object.isRequired,
    loggedIn: PropTypes.bool.isRequired,
    role: PropTypes.string,
  };

  static defaultProps = {
    role: null,
  };

  constructor(props) {
    super(props);

    this.toggle = this.toggle.bind(this);
    this.state = {
      isOpen: false,
    };

    const { loggedIn } = this.props;
    if (loggedIn) {
      this.setAutoLogout();
    }
  }

  /**
   * Manage the auto logout functionality if the loggedIn prop changes.
   * @param {*} prevProps the previous props before the component updated
   */
  componentDidUpdate(prevProps) {
    const { loggedIn } = this.props;
    if (prevProps.loggedIn !== loggedIn) {
      if (loggedIn === true) {
        this.setAutoLogout();
      } else if (this.logoutTimeout) {
        clearTimeout(this.logoutTimeout);
        this.logoutTimeout = null;
      }
    }
  }

  /**
   * Redirect the user to the logout route 10 seconds before their token expires.
   *
   * This is managed here since the Navigation component is always present, and App.jsx initializes
   * the router, so it can't cleanly redirect to the logout route.
   */
  setAutoLogout() {
    if (this.logoutTimeout) {
      return;
    }
    const { history } = this.props;

    const tokenExpiration = AuthService.getTokenExpirationDate();
    const expiresIn = tokenExpiration - new Date();
    // Redirect to the logout page 10 seconds before the token expires
    this.logoutTimeout = setTimeout(() => {
      history.push('/logout');
    }, expiresIn - 10000);
  }

  toggle() {
    const { isOpen } = this.state;
    this.setState({
      isOpen: !isOpen,
    });
  }

  render() {
    const { loggedIn, role } = this.props;
    const links = [];
    if (role === 'admin') {
      links.push(
        <NavLink tag={Link} to="/configure-questions/1">
          Configure Questions
        </NavLink>,
      );
    } else {
      if (loggedIn === false) {
        links.push(
          <NavLink tag={Link} to="/reset-with-questions">
            Forgot Password
          </NavLink>,
        );
      }
      links.push(
        <NavLink tag={Link} to="/set-answers">
          Set Answers
        </NavLink>,
      );
    }

    if (this.props.loggedIn === true) {
      links.push(
        <NavLink tag={Link} to="/logout">
          Logout
        </NavLink>,
      );
    } else {
      links.push(
        <NavLink tag={Link} to="/login">
          Login
        </NavLink>,
      );
    }

    return (
      <Navbar dark expand="sm">
        <Container>
          <NavbarBrand tag={Link} to="/">
            <img className="navbar-logo" src={logo} alt="logo" />
          </NavbarBrand>
          <NavbarToggler onClick={this.toggle} />
          <Collapse isOpen={this.state.isOpen} navbar>
            <Nav className="ml-auto" navbar>
              {links.map((link, index) => (
                // eslint-disable-next-line react/no-array-index-key
                <NavItem key={index}>{link}</NavItem>
              ))}
            </Nav>
          </Collapse>
        </Container>
      </Navbar>
    );
  }
}

export default withRouter(Navigation);

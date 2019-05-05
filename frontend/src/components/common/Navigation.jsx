import React, { Component } from 'react';
import { Link } from 'react-router-dom';
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

import './Navigation.css';
import logo from '../../imgs/logo.png';

class Navigation extends Component {
  static propTypes = {
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

export default Navigation;

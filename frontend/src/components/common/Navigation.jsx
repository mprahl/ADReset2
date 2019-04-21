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
    const loginStateLink = this.props.loggedIn ? (
      <NavLink tag={Link} to="/logout">
        Logout
      </NavLink>
    ) : (
      <NavLink tag={Link} to="/login">
        Login
      </NavLink>
    );

    return (
      <Navbar dark expand="sm">
        <Container>
          <NavbarBrand tag={Link} to="/">
            <img className="navbar-logo" src={logo} alt="logo" />
          </NavbarBrand>
          <NavbarToggler onClick={this.toggle} />
          <Collapse isOpen={this.state.isOpen} navbar>
            <Nav className="ml-auto" navbar>
              <NavItem>{loginStateLink}</NavItem>
              <NavItem>
                <NavLink href="#">Placeholder</NavLink>
              </NavItem>
            </Nav>
          </Collapse>
        </Container>
      </Navbar>
    );
  }
}

export default Navigation;

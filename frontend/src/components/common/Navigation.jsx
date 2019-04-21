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
    let loginStateLink;
    let roleSpecificLinks = [];
    if (this.props.loggedIn) {
      loginStateLink = (
        <NavLink tag={Link} to="/logout">
          Logout
        </NavLink>
      );

      if (this.props.role === 'admin') {
        roleSpecificLinks = [
          <NavLink tag={Link} to="/configure-questions/1">
            Configure Questions
          </NavLink>,
        ];
      } else if (this.props.role === 'user') {
        roleSpecificLinks = [
          <NavLink tag={Link} to="/set-answers">
            Set Answers
          </NavLink>,
        ];
      }
    } else {
      loginStateLink = (
        <NavLink tag={Link} to="/login">
          Login
        </NavLink>
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
              {roleSpecificLinks.map((link, index) => (
                // eslint-disable-next-line react/no-array-index-key
                <NavItem key={index}>{link}</NavItem>
              ))}
              <NavItem>{loginStateLink}</NavItem>
            </Nav>
          </Collapse>
        </Container>
      </Navbar>
    );
  }
}

export default Navigation;

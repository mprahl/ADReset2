/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { Component } from 'react';
import { Link, Redirect } from 'react-router-dom';
import {
  Card,
  CardBody,
  CardHeader,
  CardText,
  CardTitle,
  Container,
} from 'reactstrap';
import { PropTypes } from 'prop-types';

const cardLinkStyle = {
  display: 'block',
  height: '40px',
  marginBottom: '0.75rem',
  textDecoration: 'none',
  width: '190px',
};

class Home extends Component {
  static propTypes = {
    about: PropTypes.object,
    loggedIn: PropTypes.bool.isRequired,
    role: PropTypes.string,
  };

  static defaultProps = {
    about: {},
    role: null,
  };

  toggle = e => {
    const btnID = e.target.id;
    this.setState(oldState => {
      const tooltipOpenings = { ...oldState.tooltipOpenings };
      tooltipOpenings[btnID] = !tooltipOpenings[btnID];
      return { tooltipOpenings };
    });
  };

  render() {
    const { about, loggedIn, role } = this.props;
    if (role === 'admin') {
      return <Redirect to="/configure-questions/1" />;
    }

    return (
      <Container>
        <h2 className="text-center mb-5">Password Reset Portal</h2>
        <Card style={{ maxWidth: '900px' }}>
          <CardHeader>Getting Started</CardHeader>
          <CardBody>
            <CardTitle>About The Portal</CardTitle>
            <div style={{ maxWidth: '750px' }}>
              <CardText className="mt-4">
                ADReset allows you to reset your Windows (Active Directory) password using secret
                questions or a secondary email.
              </CardText>
              <CardText>
                To set your secret questions, click on the &quot;Set Questions&quot; button and then
                login. Your password cannot be reset using this method until your secret questions
                are set.
              </CardText>
              <CardText>
                You may also change your password without resetting it by entering your current
                password and desired new password. To do so, click on &quot;Change Password&quot;.
              </CardText>
              <CardText style={{ marginTop: '2rem' }}>Please select an option below:</CardText>
              {about.account_status_enabled === true ? (
                <Link style={cardLinkStyle} className="btn btn-primary" to="/account-status">
                  Account Status
                </Link>
              ) : null}

              <Link style={cardLinkStyle} className="btn btn-primary" to="/set-answers">
                Set Questions
              </Link>
              {!loggedIn ? (
                <React.Fragment>
                  <Link
                    style={cardLinkStyle}
                    className="btn btn-primary"
                    to="/reset-with-questions"
                  >
                    Reset With Questions
                  </Link>
                </React.Fragment>
              ) : null}
            </div>
          </CardBody>
        </Card>
      </Container>
    );
  }
}
export default Home;

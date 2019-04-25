/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { Component } from 'react';
import { Link, Redirect } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  CardText,
  CardTitle,
  Container,
  Tooltip,
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
    role: PropTypes.string,
  };

  static defaultProps = {
    role: null,
  };

  constructor(props) {
    super(props);
    this.state = {
      tooltipOpenings: {},
    };
  }

  toggle = e => {
    const btnID = e.target.id;
    this.setState(oldState => {
      const tooltipOpenings = { ...oldState.tooltipOpenings };
      tooltipOpenings[btnID] = !tooltipOpenings[btnID];
      return { tooltipOpenings };
    });
  };

  render() {
    if (this.props.role === 'admin') {
      return <Redirect to="/configure-questions/1" />;
    }

    const disabledButtons = [];
    ['Change Password', 'Reset With Questions', 'Reset With Email'].forEach((text, i) => {
      disabledButtons.push(
        // eslint-disable-next-line react/no-array-index-key
        <React.Fragment key={i}>
          <Button
            style={cardLinkStyle}
            className="btn btn-primary disabled"
            id={`disabled${i + 1}`}
          >
            {text}
          </Button>
          <Tooltip
            delay={{ show: 0, hide: 0 }}
            placement="top"
            isOpen={this.state.tooltipOpenings[`disabled${i + 1}`]}
            target={`disabled${i + 1}`}
            toggle={this.toggle}
          >
            This functionality is disabled by your administrator.
          </Tooltip>
        </React.Fragment>,
      );
    });

    return (
      <Container className="mb-5">
        <h2 className="text-center mb-5">Password Reset Portal</h2>
        <Card style={{ maxWidth: '900px' }}>
          <CardHeader>Getting Started</CardHeader>
          <CardBody>
            <CardTitle>About The Portal</CardTitle>
            <div style={{ maxWidth: '750px' }}>
              <CardText className="mt-4">
                ADReset allows you to reset your Windows (Active Directory) password via secret
                questions or a secondary email.
              </CardText>
              <CardText>
                To set your secret questions, click on the &quot;Set Questions&quot; button and then
                login. Your password cannot be reset using this method until your secret questions
                are set.
              </CardText>
              <CardText>
                You may also simply change your password without resetting it by simply entering
                your current password and your new password. To do so, simply click on &quot;Change
                Password&quot;.
              </CardText>
              <CardText style={{ marginTop: '2rem' }}>Please select an option below:</CardText>
              <Link style={cardLinkStyle} className="btn btn-primary" to="/set-answers">
                Set Questions
              </Link>
              {disabledButtons}
            </div>
          </CardBody>
        </Card>
      </Container>
    );
  }
}
export default Home;

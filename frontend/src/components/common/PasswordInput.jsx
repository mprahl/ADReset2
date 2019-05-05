import React, { Component } from 'react';
import { Input, InputGroup, InputGroupAddon, InputGroupText } from 'reactstrap';
import Visibility from '@material-ui/icons/Visibility';
import VisibilityOff from '@material-ui/icons/VisibilityOff';

/**
 * Creates a password input with a hide/show button.
 *
 * @class PasswordInput
 * @extends {Component}
 */
class PasswordInput extends Component {
  static defaultProps = {
    disabled: false,
    className: '',
  };

  constructor(props) {
    super(props);
    this.state = {
      visible: false,
    };
  }

  /**
   * Toggles the visibility of the input field.
   */
  toggleVisibility = () => {
    const { disabled } = this.props;
    // Don't change the visibility when the input is disabled
    if (disabled) {
      return;
    }
    this.setState(oldState => ({ visible: !oldState.visible }));
  };

  render() {
    const { visible } = this.state;
    const { className, ...props } = this.props;
    const { disabled } = this.props;

    return (
      <InputGroup className={className}>
        <Input type={!visible || disabled ? 'password' : 'text'} {...props} />
        <InputGroupAddon addonType="append">
          <InputGroupText
            onClick={this.toggleVisibility}
            style={{ cursor: disabled ? 'initial' : 'pointer' }}
          >
            {!visible || disabled ? <VisibilityOff /> : <Visibility />}
          </InputGroupText>
        </InputGroupAddon>
      </InputGroup>
    );
  }
}

export default PasswordInput;

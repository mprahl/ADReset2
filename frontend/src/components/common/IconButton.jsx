import React from 'react';
import { Button } from 'reactstrap';
import CircularProgress from '@material-ui/core/CircularProgress';
import { PropTypes } from 'prop-types';

const iconStyles = { marginRight: '7.5px', color: '#fff' };


/**
 * Creates a button with an icon and text, with spinner support.
 *
 * @param {*} props The React props to configure the button.
 */
const IconButton = ({
  buttonClassName,
  clickHandler,
  children,
  disabled,
  Icon,
  loading,
  primary,
}) => (
  <Button
    className={buttonClassName}
    disabled={disabled}
    onClick={clickHandler}
    color={primary === true ? 'primary' : 'secondary'}
    style={{
      marginRight: '0.5rem',
      width: '110px',
    }}
  >
    {loading ? <CircularProgress size="24px" style={iconStyles} /> : <Icon style={iconStyles} />}
    {children}
  </Button>
);

IconButton.propTypes = {
  buttonClassName: PropTypes.string,
  clickHandler: PropTypes.func,
  children: PropTypes.node.isRequired,
  disabled: PropTypes.bool,
  Icon: PropTypes.any.isRequired,
  loading: PropTypes.bool.isRequired,
  primary: PropTypes.bool,
};

IconButton.defaultProps = {
  buttonClassName: '',
  clickHandler: null,
  disabled: false,
  primary: true,
};

export default IconButton;

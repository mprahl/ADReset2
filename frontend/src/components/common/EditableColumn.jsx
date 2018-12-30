import React, { Component } from 'react';
import { PropTypes } from 'prop-types';
import { Button } from 'reactstrap';
import CheckCircle from '@material-ui/icons/CheckCircle';
import Cancel from '@material-ui/icons/Cancel';

import './EditableColumn.css';


class EditableColumn extends Component {
  static propTypes = {
    displayToast: PropTypes.func.isRequired,
    id: PropTypes.number.isRequired,
    column: PropTypes.string.isRequired,
    value: PropTypes.string.isRequired,
    update: PropTypes.func.isRequired,
    done: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props);
    this.state = {
      loading: false,
      value: props.value,
    };
    this.update = this.update.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.handleKeyUp = this.handleKeyUp.bind(this);
  }

  update() {
    this.setState({ loading: true });
    const { id } = this.props;
    if (this.props.value === this.state.value) {
      this.props.done();
      return;
    }

    this.props.update(id, { question: this.state.value })
      .then((data) => {
        this.props.displayToast('success', `The ${this.props.column} was updated`);
        this.props.done(this.props.id, this.props.column, data[this.props.column]);
      })
      .catch((error) => {
        this.props.displayToast('error', error.message);
        this.setState({ loading: false });
      });
  }

  // eslint-disable-next-line class-methods-use-this
  handleKeyUp(event) {
    if (event.keyCode === 13) {
      // Submit using the enter key
      const editBtn = event.target.parentElement.querySelector('button.edit-btn');
      editBtn.click();
    } else if (event.keyCode === 27) {
      // Cancel using the escape key
      const editBtn = event.target.parentElement.querySelector('button.cancel-btn');
      editBtn.click();
    }
  }

  handleChange(event) {
    this.setState({ value: event.target.value });
  }

  render() {
    return (
      <td>
        <input
          value={this.state.value}
          onChange={this.handleChange}
          onKeyUp={this.handleKeyUp}
          placeholder={`Set the ${this.props.column}`}
          className="form-control editable-input"
          disabled={this.state.loading}
        />
        <Button
          onClick={this.update}
          color="link"
          className="editable-btn edit-btn"
          disabled={this.state.loading}
        >
          <CheckCircle />
        </Button>
        <Button
          onClick={() => { this.props.done(); }}
          color="link"
          className="editable-btn cancel-btn"
          disabled={this.state.loading}
        >
          <Cancel />
        </Button>
      </td>
    );
  }
}


export default EditableColumn;

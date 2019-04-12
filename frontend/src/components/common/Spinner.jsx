import React from 'react';
import CircularProgress from '@material-ui/core/CircularProgress';

import './Spinner.css';

function Spinner() {
  return (
    <div className="spinner-container">
      <CircularProgress className="spinner" size="45px" />
    </div>
  );
}

export default Spinner;

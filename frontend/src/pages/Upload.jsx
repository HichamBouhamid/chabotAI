import React from 'react';
import DropFileInput from '../components/Drop-File/DropFileInput';
import dxcIcon from '../assets/dxc.png';

const UploadPage = ({ onFileChange }) => {
    return (
        <div className="w-screen h-screen flex justify-center bg-[#f0f4f9]">
            <div className="max-w-sm mx-auto">
                <div className="flex justify-center">
                    <img src={dxcIcon} alt="DXC Logo" className="my-5 h-50 w-50" />
                </div>
                <div>
                    <h2 className='flex justify-center my-3'>
                        Upload your PDF here
                    </h2>
                    <DropFileInput
                        onFileChange={onFileChange}
                    />
                </div>
            </div>
        </div>
    );
};

export default UploadPage;

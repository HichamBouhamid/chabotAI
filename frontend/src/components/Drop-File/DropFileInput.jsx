import React, { useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { ImageConfig } from '../../config/ImageConfig';
import uploadImg from '../../assets/cloud-upload-regular-240.png';
import { useNavigate } from 'react-router-dom';

const DropFileInput = (props) => {
    const wrapperRef = useRef(null);
    const [fileList, setFileList] = useState([]);
    const navigate = useNavigate();

    const onDragEnter = () => wrapperRef.current.classList.add('dragover');
    const onDragLeave = () => wrapperRef.current.classList.remove('dragover');
    const onDrop = () => wrapperRef.current.classList.remove('dragover');

    const onFileDrop = (e) => {
        const newFile = e.target.files[0];
        if (newFile) {
            const updatedList = [...fileList, newFile];
            setFileList(updatedList);
            props.onFileChange(updatedList);
        }
    };

    const fileRemove = (file) => {
        const updatedList = fileList.filter((item) => item !== file);
        setFileList(updatedList);
        props.onFileChange(updatedList);
    };

    const uploadFiles = () => {
        const formData = new FormData();
        fileList.forEach((file) => formData.append('file', file));
        fetch('/upload', {
            method: 'POST',
            body: formData,
        })
            .then((response) => {
                if (response.ok) {
                    // Handle success response, e.g., redirect or show a success message
                    navigate('/chat');
                } else {
                    // Handle error response
                }
            })
            .catch((error) => {
                // Handle network error
            });
    };

    return (
        <>
            <div
                ref={wrapperRef}
                className="relative w-96 h-52 border-2 border-dashed border-gray-300 rounded-2xl flex items-center justify-center bg-gray-100 transition-opacity duration-300 hover:opacity-60 dragover:opacity-60"
                onDragEnter={onDragEnter}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
            >
                <div className="text-center text-gray-500 font-semibold p-2">
                    <img src={uploadImg} alt="" className="w-24 mx-auto" />
                    <p>Drag & Drop your files here</p>
                </div>
                <input
                    type="file"
                    className="opacity-0 absolute top-0 left-0 w-full h-full cursor-pointer"
                    onChange={onFileDrop}
                />
            </div>
            {fileList.length > 0 && (
                <div className="mt-4">
                    <p className="font-medium mx-4 ">Ready to upload</p>
                    <div className="overflow-y-auto max-h-40">
                        {fileList.map((item, index) => (
                            <div key={index} className="relative flex mb-2 bg-gray-100 p-4 rounded-2xl">
                                <img src={ImageConfig[item.type.split('/')[1]] || ImageConfig['default']} alt="" className="w-12 h-12 mr-5" />
                                <div className="flex flex-col justify-between">
                                    <p className="font-medium">{item.name}</p>
                                    <p className="font-medium">{item.size}B</p>                      
                                </div>
                                <span
                                    className="absolute right-3 top-1/2 transform -translate-y-1/2 bg-gray-200 w-10 h-10 rounded-full flex items-center justify-center cursor-pointer shadow-lg opacity-4  transition-opacity duration-300 hover:opacity-100"
                                    onClick={() => fileRemove(item)}
                                >
                                    x
                                </span>
                            </div>
                        ))}
                    </div>
                    <button
                        className="block mx-auto mt-8 px-5 py-2.5 bg-purple-700 text-white text-center text-base font-bold rounded-md hover:bg-blue-700"
                        onClick={uploadFiles}
                    >
                        Upload
                    </button>
                </div>
            )}
        </>
    );
};

DropFileInput.propTypes = {
    onFileChange: PropTypes.func.isRequired,
};

export default DropFileInput;

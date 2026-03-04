import React, { useState, useRef } from 'react';
import ReactCrop, { Crop, PixelCrop, centerCrop, makeAspectCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { Button } from './Button';
import { Modal } from './Modal';
import { useTheme } from '../../contexts/ThemeContext';
import { THEMES } from '../../constants';

interface ImageCropperProps {
    isOpen: boolean;
    imageUrl: string;
    onClose: () => void;
    onCropComplete: (croppedBase64: string) => void;
}

function centerAspectCrop(
    mediaWidth: number,
    mediaHeight: number,
    aspect: number,
) {
    return centerCrop(
        makeAspectCrop(
            {
                unit: '%',
                width: 90,
            },
            aspect,
            mediaWidth,
            mediaHeight,
        ),
        mediaWidth,
        mediaHeight,
    )
}

export const ImageCropper: React.FC<ImageCropperProps> = ({
    isOpen,
    imageUrl,
    onClose,
    onCropComplete
}) => {
    const { style } = useTheme();
    const isNeo = style === THEMES.NEOBRUTALISM;
    const [crop, setCrop] = useState<Crop>();
    const [completedCrop, setCompletedCrop] = useState<PixelCrop>();
    const imgRef = useRef<HTMLImageElement>(null);

    const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
        const { width, height } = e.currentTarget;
        setCrop(centerAspectCrop(width, height, 1));
    };

    const handleSave = () => {
        if (!completedCrop || !imgRef.current) {
            return;
        }

        const canvas = document.createElement('canvas');
        const scaleX = imgRef.current.naturalWidth / imgRef.current.width;
        const scaleY = imgRef.current.naturalHeight / imgRef.current.height;

        canvas.width = completedCrop.width;
        canvas.height = completedCrop.height;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            return;
        }

        ctx.drawImage(
            imgRef.current,
            completedCrop.x * scaleX,
            completedCrop.y * scaleY,
            completedCrop.width * scaleX,
            completedCrop.height * scaleY,
            0,
            0,
            completedCrop.width,
            completedCrop.height
        );

        const base64Image = canvas.toDataURL('image/jpeg', 0.9);
        onCropComplete(base64Image);
        onClose();
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Crop Image"
            footer={
                <>
                    <Button variant="ghost" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={!completedCrop}>
                        Apply
                    </Button>
                </>
            }
        >
            <div className="flex flex-col items-center justify-center p-4">
                {imageUrl && (
                    <div className={`max-h-[60vh] overflow-hidden ${isNeo ? 'border-4 border-black' : 'rounded-lg overflow-hidden border border-white/20'}`}>
                        <ReactCrop
                            crop={crop}
                            onChange={(_, percentCrop) => setCrop(percentCrop)}
                            onComplete={(c) => setCompletedCrop(c)}
                            aspect={1}
                            circularCrop
                        >
                            <img
                                ref={imgRef}
                                src={imageUrl}
                                onLoad={onImageLoad}
                                alt="Crop me"
                                className="max-w-full max-h-[50vh] object-contain"
                            />
                        </ReactCrop>
                    </div>
                )}
                <p className="mt-4 text-sm opacity-60">Drag to adjust the circular crop area</p>
            </div>
        </Modal>
    );
};

import { motion } from 'framer-motion';
import { Camera, ChevronRight, CreditCard, LogOut, Mail, MessageSquare, Settings, Shield, User } from 'lucide-react';
import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { THEMES } from '../constants';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../contexts/ToastContext';
import { updateProfile } from '../services/api';

export const Profile = () => {
    const { user, logout, updateUserInContext } = useAuth();
    const { style } = useTheme();
    const { addToast } = useToast();
    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editName, setEditName] = useState(user?.name || '');
    const [pickedImage, setPickedImage] = useState<{ url: string; base64: string } | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);

    const handleImagePick = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            setSaveError('Image must be less than 5MB');
            return;
        }

        if (!file.type.startsWith('image/')) {
            setSaveError('Please select a valid image file');
            return;
        }

        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result as string;
            setPickedImage({ url: result, base64: result });
        };
        reader.readAsDataURL(file);
    };

    const handleSaveProfile = async () => {
        if (!editName.trim()) {
            setSaveError('Name cannot be empty');
            return;
        }

        setSaveError(null);
        setIsSaving(true);
        try {
            const updates: { name?: string; imageUrl?: string } = {};
            if (editName !== user?.name) {
                updates.name = editName;
            }
            if (pickedImage?.base64) {
                updates.imageUrl = pickedImage.base64;
            }

            if (Object.keys(updates).length > 0) {
                const response = await updateProfile(updates);
                const updatedUser = { ...user!, ...updates, ...(response.data || {}) };
                updateUserInContext(updatedUser);
            }
            setIsEditModalOpen(false);
            addToast('Profile updated successfully!', 'success');
        } catch (error) {
            console.error('Failed to update profile:', error);
            setSaveError('Failed to update profile. Please try again.');
            addToast('Failed to update profile', 'error');
        } finally {
            setIsSaving(false);
        }
    };

    const openEditModal = () => {
        setEditName(user?.name || '');
        setPickedImage(null);
        setIsEditModalOpen(true);
    };

    const handleComingSoon = () => {
        alert('This feature is coming soon!');
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const avatarUrl = pickedImage?.url || user?.imageUrl;
    const isValidImageUrl = avatarUrl && /^(https?:|data:image)/.test(avatarUrl);
    const isNeo = style === THEMES.NEOBRUTALISM;

    const menuSections = [
        {
            title: 'Account',
            items: [
                { label: 'Edit Profile', icon: User, onClick: openEditModal, desc: 'Update your personal info' },
                { label: 'Email Settings', icon: Mail, onClick: handleComingSoon, desc: 'Manage email preferences' },
                { label: 'Security', icon: Shield, onClick: handleComingSoon, desc: 'Password and 2FA' },
            ]
        },
        {
            title: 'App',
            items: [
                { label: 'Appearance', icon: Settings, onClick: handleComingSoon, desc: 'Theme and display settings' },
                { label: 'Send Feedback', icon: MessageSquare, onClick: handleComingSoon, desc: 'Help us improve' },
            ]
        }
    ];

    return (
        <div className="min-h-screen pb-20">
            {/* Hero Header */}
            <div className="relative h-64 w-full overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-purple-700 dark:from-blue-900 dark:to-purple-900" />
                {/* Abstract shapes */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                <div className="absolute bottom-0 left-0 w-48 h-48 bg-black/10 rounded-full blur-2xl translate-y-1/2 -translate-x-1/2" />

                <div className="absolute inset-0 flex items-center justify-center">
                    <h1 className="text-white/20 text-9xl font-black tracking-tighter select-none">PROFILE</h1>
                </div>
            </div>

            <div className="max-w-3xl mx-auto px-6 -mt-20 relative z-10">
                {/* Profile Card */}
                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className={`p-6 mb-8 ${isNeo
                            ? 'bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] rounded-none'
                            : 'bg-white/80 dark:bg-black/40 backdrop-blur-xl border border-white/20 shadow-2xl rounded-3xl'
                        }`}
                >
                    <div className="flex flex-col md:flex-row items-center gap-6">
                        <div
                            className="relative group cursor-pointer"
                            onClick={openEditModal}
                            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openEditModal(); } }}
                            tabIndex={0}
                            role="button"
                            aria-label="Edit profile picture"
                        >
                            <div className={`w-32 h-32 p-1 ${isNeo ? 'bg-black rounded-none' : 'bg-gradient-to-br from-blue-500 to-purple-500 rounded-full'}`}>
                                {isValidImageUrl ? (
                                    <img
                                        src={avatarUrl}
                                        alt={user?.name}
                                        className={`w-full h-full object-cover border-4 border-white dark:border-gray-900 ${isNeo ? 'rounded-none' : 'rounded-full'}`}
                                    />
                                ) : (
                                    <div className={`w-full h-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-4xl font-bold text-gray-500 border-4 border-white dark:border-gray-900 ${isNeo ? 'rounded-none' : 'rounded-full'}`}>
                                        {user?.name?.charAt(0) || 'A'}
                                    </div>
                                )}
                            </div>
                            <div className={`absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity ${isNeo ? 'rounded-none' : 'rounded-full'}`}>
                                <div className="bg-black/50 p-2 text-white rounded-full">
                                    <Camera size={24} />
                                </div>
                            </div>
                        </div>

                        <div className="flex-1 text-center md:text-left">
                            <h2 className="text-3xl font-black mb-1">{user?.name}</h2>
                            <p className="opacity-60 font-medium mb-4">{user?.email}</p>
                            <div className="flex flex-wrap justify-center md:justify-start gap-3">
                                <div className={`px-4 py-2 text-sm font-bold flex items-center gap-2 ${isNeo ? 'bg-yellow-200 border-2 border-black rounded-none' : 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 rounded-xl'
                                    }`}>
                                    <CreditCard size={16} />
                                    <span>Pro Member</span>
                                </div>
                                <div className={`px-4 py-2 text-sm font-bold flex items-center gap-2 ${isNeo ? 'bg-blue-200 border-2 border-black rounded-none' : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-xl'
                                    }`}>
                                    <Shield size={16} />
                                    <span>Verified</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Menu Sections */}
                <div className="space-y-6">
                    {menuSections.map((section, idx) => (
                        <motion.div
                            key={section.title}
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.1 + (idx * 0.1) }}
                        >
                            <h3 className="text-sm font-bold uppercase tracking-wider opacity-50 mb-3 ml-2">{section.title}</h3>
                            <div className={`overflow-hidden ${isNeo
                                    ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
                                    : 'bg-white/5 border border-white/10 backdrop-blur-sm rounded-2xl'
                                }`}>
                                {section.items.map((item, itemIdx) => (
                                    <button
                                        type="button"
                                        key={item.label}
                                        onClick={item.onClick}
                                        className={`w-full flex items-center gap-4 p-4 transition-all hover:bg-black/5 dark:hover:bg-white/5 ${itemIdx !== section.items.length - 1 ? 'border-b border-gray-200/50 dark:border-gray-700/50' : ''
                                            }`}
                                    >
                                        <div className={`w-10 h-10 flex items-center justify-center ${isNeo ? 'bg-black text-white rounded-none' : 'bg-white/10 rounded-full'
                                            }`}>
                                            <item.icon size={20} />
                                        </div>
                                        <div className="flex-1 text-left">
                                            <h4 className="font-bold">{item.label}</h4>
                                            <p className="text-xs opacity-60">{item.desc}</p>
                                        </div>
                                        <ChevronRight size={18} className="opacity-30" />
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    ))}

                    <motion.button
                        type="button"
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        onClick={handleLogout}
                        className={`w-full p-4 font-bold flex items-center justify-center gap-2 transition-all group ${isNeo
                                ? 'bg-red-500 text-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] rounded-none'
                                : 'bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white border border-red-500/20 rounded-2xl'
                            }`}
                    >
                        <LogOut size={20} />
                        <span>Log Out</span>
                    </motion.button>
                </div>
            </div>

            {/* Edit Profile Modal */}
            <Modal
                isOpen={isEditModalOpen}
                onClose={() => setIsEditModalOpen(false)}
                title="Edit Profile"
                footer={
                    <>
                        <Button variant="ghost" onClick={() => setIsEditModalOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleSaveProfile} disabled={isSaving}>
                            {isSaving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </>
                }
            >
                <div className="space-y-6">
                    {saveError && (
                        <div className="p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg text-sm text-center">
                            {saveError}
                        </div>
                    )}
                    <div className="flex flex-col items-center">
                        <div
                            className="relative mb-4 group cursor-pointer"
                            onClick={() => fileInputRef.current?.click()}
                            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInputRef.current?.click(); } }}
                            tabIndex={0}
                            role="button"
                            aria-label="Change profile photo"
                        >
                            {pickedImage?.url || (user?.imageUrl && /^(https?:|data:image)/.test(user.imageUrl)) ? (
                                <img
                                    src={pickedImage?.url || user?.imageUrl}
                                    alt="Profile"
                                    className={`w-32 h-32 object-cover border-4 border-gray-100 dark:border-gray-800 ${isNeo ? 'rounded-none' : 'rounded-full'}`}
                                />
                            ) : (
                                <div className={`w-32 h-32 flex items-center justify-center text-4xl font-bold text-white bg-gradient-to-br from-blue-500 to-purple-600 ${isNeo ? 'rounded-none' : 'rounded-full'}`}>
                                    {editName?.charAt(0) || user?.name?.charAt(0) || 'A'}
                                </div>
                            )}
                            <div className={`absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity ${isNeo ? 'rounded-none' : 'rounded-full'}`}>
                                <Camera className="text-white" size={32} />
                            </div>
                        </div>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            onChange={handleImagePick}
                            className="hidden"
                        />
                        <p className="text-sm opacity-50">Click to change photo</p>
                    </div>

                    <Input
                        label="Display Name"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        placeholder="Enter your name"
                        required
                        className={isNeo ? 'rounded-none' : ''}
                    />
                </div>
            </Modal>
        </div>
    );
};

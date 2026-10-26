import { Toaster as Sonner, ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast: "!rounded-md !border !border-line-strong !bg-surface-2 !font-sans !text-text-primary",
          description: "!text-text-secondary",
          success: "[&_[data-icon]]:!text-success",
          error: "[&_[data-icon]]:!text-danger",
          info: "[&_[data-icon]]:!text-cyan",
          closeButton: "!border-line-strong !bg-surface-3 !text-text-secondary",
        },
      }}
      {...props}
    />
  );
};

export { Toaster };

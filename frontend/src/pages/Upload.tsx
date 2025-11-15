import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload as UploadIcon, Image, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { HistoryBar } from "@/components/ui/history-bar";

export default function Upload() {
  const [name, setName] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    if (file.type.startsWith("image/")) {
      setUploadedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      toast({
        title: "File uploaded",
        description: `${file.name} has been uploaded successfully.`,
      });
    } else {
      toast({
        title: "Invalid file type",
        description: "Please upload an image file.",
        variant: "destructive",
      });
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
    setPreviewUrl("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  if (!uploadedFile) {
    toast({
      title: "Photo required",
      description: "Please upload a photo before submitting.",
      variant: "destructive",
    });
    return;
  }

  try {
    const formData = new FormData();
    formData.append("file", uploadedFile);

    toast({
      title: "Processing...",
      description: "Running the face recognition model.",
    });

    const response = await fetch("http://localhost:8000/match", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!data.success) {
      toast({
        title: "No matches found",
        description: "Try uploading a clearer photo.",
        variant: "destructive",
      });
      return;
    }

    // Save results in localStorage for dashboard page
    localStorage.setItem("face_results", JSON.stringify(data.results));

    toast({
      title: "Recognition Complete",
      description: "Redirecting to dashboard...",
    });

    navigate("/dashboard");

  } catch (error) {
    console.error(error);
    toast({
      title: "Error",
      description: "Backend not running or server error occurred.",
      variant: "destructive",
    });
  }
};


  const handleNewUpload = () => {
    setName("");
    removeFile();
  };

  return (
    <div className="space-y-0">
      <HistoryBar onNewUpload={handleNewUpload} />
      
      <div className="p-4 sm:p-6 space-y-6 sm:space-y-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Upload Identity</h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            Upload a photo to start the identity recognition process
          </p>
        </div>

      <div className="grid gap-6 sm:gap-8 md:grid-cols-2">
        {/* Name Input */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-lg sm:text-xl">Personal Information</CardTitle>
            <CardDescription className="text-sm">
              Enter the name associated with the identity
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="Enter name here"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="text-base sm:text-sm"
              />
            </div>
          </CardContent>
        </Card>

        {/* File Upload */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-lg sm:text-xl">Photo Upload</CardTitle>
            <CardDescription className="text-sm">
              Drag and drop or click to upload an image
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div
                className={`relative border-2 border-dashed rounded-lg p-4 sm:p-6 transition-colors ${
                  dragActive
                    ? "border-primary bg-primary-muted"
                    : "border-border hover:border-primary hover:bg-accent"
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple={false}
                  accept="image/*"
                  onChange={handleChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="text-center">
                  <UploadIcon className="mx-auto h-10 w-10 sm:h-12 sm:w-12 text-muted-foreground" />
                  <div className="mt-3 sm:mt-4">
                    <p className="text-sm font-medium">Upload Photo</p>
                    <p className="text-xs text-muted-foreground">
                      Drag & Drop or click to browse
                    </p>
                  </div>
                </div>
              </div>

              {/* File Preview */}
              {uploadedFile && previewUrl && (
                <div className="relative">
                  <div className="relative overflow-hidden rounded-lg border border-border">
                    <img
                      src={previewUrl}
                      alt="Upload preview"
                      className="w-full h-40 sm:h-48 object-cover"
                    />
                    <Button
                      variant="destructive"
                      size="sm"
                      className="absolute top-2 right-2"
                      onClick={removeFile}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2 truncate">
                    {uploadedFile.name}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Submit Button */}
      <div className="flex justify-center sm:justify-end">
        <Button onClick={handleSubmit} className="w-full sm:w-auto min-w-32" size="lg">
          <UploadIcon className="mr-2 h-4 w-4" />
          Start Recognition
        </Button>
      </div>
      </div>
    </div>
  );
}
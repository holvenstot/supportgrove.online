import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog.jsx'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible.jsx'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu.jsx'
import { Heart, MessageCircle, Sparkles, Search, Plus, Hash, AlertTriangle, Users, Shield, Leaf, Bell, ChevronDown, ChevronUp, Reply, Send, Share, Copy, Mail, ExternalLink } from 'lucide-react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5002/api'

function App() {
  const [stories, setStories] = useState([])
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isShareDialogOpen, setIsShareDialogOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentView, setCurrentView] = useState('home') // home, browse
  
  // Commenting system state
  const [comments, setComments] = useState({}) // story_id -> comments array
  const [expandedComments, setExpandedComments] = useState({}) // story_id -> boolean
  const [replyingTo, setReplyingTo] = useState(null) // comment_id or null
  const [commentContent, setCommentContent] = useState('')
  const [commentPseudonym, setCommentPseudonym] = useState('')
  
  // Notification system state
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [showNotifications, setShowNotifications] = useState(false)
  
  // Forwarding system state
  const [isForwardDialogOpen, setIsForwardDialogOpen] = useState(false)
  const [forwardingStory, setForwardingStory] = useState(null)
  const [forwardMethod, setForwardMethod] = useState('link') // 'link', 'email'
  const [forwardEmail, setForwardEmail] = useState('')
  const [forwardSenderName, setForwardSenderName] = useState('')
  const [forwardMessage, setForwardMessage] = useState('')
  const [shareUrl, setShareUrl] = useState('')
  const [forwardLoading, setForwardLoading] = useState(false)

  // Anonymous user ID for reactions (stored in localStorage)
  const [anonymousId] = useState(() => {
    let id = localStorage.getItem('supportgrove_anonymous_id')
    if (!id) {
      id = 'anon_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36)
      localStorage.setItem('supportgrove_anonymous_id', id)
    }
    return id
  })

  // Fetch categories and stories on load
  useEffect(() => {
    fetchData()
    fetchNotifications()
    // Poll for new notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch categories
      const categoriesResponse = await fetch(`${API_BASE}/categories`)
      const categoriesData = await categoriesResponse.json()
      
      if (categoriesData.success) {
        setCategories(categoriesData.categories)
      }

      // Fetch stories
      const storiesResponse = await fetch(`${API_BASE}/stories`)
      const storiesData = await storiesResponse.json()
      
      if (storiesData.success) {
        setStories(storiesData.stories)
      }
    } catch (err) {
      setError('Failed to load data. Please try again.')
      console.error('Error fetching data:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchNotifications = async () => {
    try {
      const response = await fetch(`${API_BASE}/notifications`, {
        headers: {
          'X-Anonymous-ID': anonymousId
        }
      })
      const data = await response.json()
      
      if (data.success) {
        setNotifications(data.notifications)
        setUnreadCount(data.unread_count)
      }
    } catch (err) {
      console.error('Error fetching notifications:', err)
    }
  }

  const fetchComments = async (storyId) => {
    try {
      const response = await fetch(`${API_BASE}/stories/${storyId}/comments`)
      const data = await response.json()
      
      if (data.success) {
        setComments(prev => ({
          ...prev,
          [storyId]: data.comments
        }))
      }
    } catch (err) {
      console.error('Error fetching comments:', err)
    }
  }

  const toggleComments = async (storyId) => {
    const isExpanded = expandedComments[storyId]
    
    if (!isExpanded) {
      // Load comments when expanding
      await fetchComments(storyId)
    }
    
    setExpandedComments(prev => ({
      ...prev,
      [storyId]: !isExpanded
    }))
  }

  const submitComment = async (storyId, parentCommentId = null) => {
    if (!commentContent.trim()) return

    try {
      const endpoint = parentCommentId 
        ? `${API_BASE}/comments/${parentCommentId}/replies`
        : `${API_BASE}/stories/${storyId}/comments`

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Anonymous-ID': anonymousId
        },
        body: JSON.stringify({
          content: commentContent.trim(),
          pseudonym: commentPseudonym.trim() || undefined
        })
      })

      const data = await response.json()
      
      if (data.success) {
        // Refresh comments for this story
        await fetchComments(storyId)
        setCommentContent('')
        setCommentPseudonym('')
        setReplyingTo(null)
      }
    } catch (err) {
      console.error('Error submitting comment:', err)
    }
  }

  const toggleCommentReaction = async (commentId, reactionType) => {
    try {
      const response = await fetch(`${API_BASE}/comments/${commentId}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Anonymous-ID': anonymousId
        },
        body: JSON.stringify({
          reaction_type: reactionType
        })
      })

      const data = await response.json()
      
      if (data.success) {
        // Update the comment in state with new reaction counts
        setComments(prev => {
          const newComments = { ...prev }
          Object.keys(newComments).forEach(storyId => {
            newComments[storyId] = newComments[storyId].map(comment => {
              if (comment.id === commentId) {
                return { ...comment, reaction_counts: data.reaction_counts }
              }
              // Also check replies
              if (comment.replies) {
                comment.replies = comment.replies.map(reply => {
                  if (reply.id === commentId) {
                    return { ...reply, reaction_counts: data.reaction_counts }
                  }
                  return reply
                })
              }
              return comment
            })
          })
          return newComments
        })
      }
    } catch (err) {
      console.error('Error toggling reaction:', err)
    }
  }

  const markNotificationRead = async (notificationId) => {
    try {
      await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
        method: 'PUT',
        headers: {
          'X-Anonymous-ID': anonymousId
        }
      })
      
      // Update local state
      setNotifications(prev => 
        prev.map(notif => 
          notif.id === notificationId 
            ? { ...notif, is_read: true }
            : notif
        )
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (err) {
      console.error('Error marking notification as read:', err)
    }
  }

  const markAllNotificationsRead = async () => {
    try {
      await fetch(`${API_BASE}/notifications/read-all`, {
        method: 'PUT',
        headers: {
          'X-Anonymous-ID': anonymousId
        }
      })
      
      setNotifications(prev => 
        prev.map(notif => ({ ...notif, is_read: true }))
      )
      setUnreadCount(0)
    } catch (err) {
      console.error('Error marking all notifications as read:', err)
    }
  }

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInSeconds = Math.floor((now - date) / 1000)
    
    if (diffInSeconds < 60) return 'Just now'
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
    return `${Math.floor(diffInSeconds / 86400)}d ago`
  }

  // Share story functionality (existing)
  const [shareStep, setShareStep] = useState(1) // 1: basic info, 2: guided questions
  const [shareForm, setShareForm] = useState({
    title: '',
    category: '',
    content: '',
    hashtags: '',
    pseudonym: '',
    healingProcess: '',
    nextSteps: ''
  })

  const handleShareSubmit = async () => {
    if (shareStep === 1) {
      if (!shareForm.title || !shareForm.category || !shareForm.content) {
        alert('Please fill in all required fields')
        return
      }
      setShareStep(2)
      return
    }

    // Step 2: Submit the complete story
    try {
      const response = await fetch(`${API_BASE}/stories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Anonymous-ID': anonymousId
        },
        body: JSON.stringify({
          title: shareForm.title,
          content: shareForm.content,
          category_id: parseInt(shareForm.category),
          hashtags: shareForm.hashtags,
          pseudonym: shareForm.pseudonym || undefined,
          healing_process: shareForm.healingProcess,
          next_steps: shareForm.nextSteps
        })
      })

      const data = await response.json()
      
      if (data.success) {
        setIsShareDialogOpen(false)
        setShareStep(1)
        setShareForm({
          title: '', category: '', content: '', hashtags: '', pseudonym: '',
          healingProcess: '', nextSteps: ''
        })
        fetchData() // Refresh stories
      }
    } catch (err) {
      console.error('Error sharing story:', err)
    }
  }

  const toggleStoryReaction = async (storyId, reactionType) => {
    try {
      const response = await fetch(`${API_BASE}/stories/${storyId}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Anonymous-ID': anonymousId
        },
        body: JSON.stringify({
          reaction_type: reactionType
        })
      })

      const data = await response.json()
      
      if (data.success) {
        setStories(prev => prev.map(story => 
          story.id === storyId 
            ? { 
                ...story, 
                heart_count: data.reaction_counts.heart,
                hug_count: data.reaction_counts.hug,
                strength_count: data.reaction_counts.strength
              }
            : story
        ))
      }
    } catch (err) {
      console.error('Error toggling reaction:', err)
    }
  }

  // Forwarding functionality
  const openForwardDialog = (story) => {
    setForwardingStory(story)
    setIsForwardDialogOpen(true)
    setForwardMethod('link')
    setForwardEmail('')
    setForwardSenderName('')
    setForwardMessage('')
    setShareUrl('')
  }

  const createShareLink = async () => {
    if (!forwardingStory) return
    
    setForwardLoading(true)
    try {
      const response = await fetch(`${API_BASE}/stories/${forwardingStory.id}/share-link`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          shared_by: forwardSenderName.trim() || undefined,
          personal_message: forwardMessage.trim() || undefined
        })
      })

      const data = await response.json()
      
      if (data.success) {
        setShareUrl(data.share_url)
        return data.share_url
      } else {
        alert('Failed to create share link')
      }
    } catch (err) {
      console.error('Error creating share link:', err)
      alert('Error creating share link')
    } finally {
      setForwardLoading(false)
    }
  }

  const sendEmailForward = async () => {
    if (!forwardingStory || !forwardEmail.trim()) return
    
    setForwardLoading(true)
    try {
      const response = await fetch(`${API_BASE}/stories/${forwardingStory.id}/forward/email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          recipient_email: forwardEmail.trim(),
          sender_name: forwardSenderName.trim() || undefined,
          personal_message: forwardMessage.trim() || undefined
        })
      })

      const data = await response.json()
      
      if (data.success) {
        alert('Story forwarded successfully via email!')
        setIsForwardDialogOpen(false)
      } else {
        alert('Failed to send email: ' + (data.error || 'Unknown error'))
      }
    } catch (err) {
      console.error('Error sending email:', err)
      alert('Error sending email')
    } finally {
      setForwardLoading(false)
    }
  }

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      alert('Link copied to clipboard!')
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      alert('Link copied to clipboard!')
    }
  }

  const handleForwardSubmit = async () => {
    if (forwardMethod === 'email') {
      if (!forwardEmail.trim()) {
        alert('Please enter a recipient email address')
        return
      }
      await sendEmailForward()
    } else {
      const url = shareUrl || await createShareLink()
      if (url) {
        await copyToClipboard(url)
      }
    }
  }

  const filteredStories = stories.filter(story => {
    const matchesCategory = !selectedCategory || story.category.id === selectedCategory
    const matchesSearch = !searchQuery || 
      story.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      story.hashtags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    return matchesCategory && matchesSearch
  })

  const CommentCard = ({ comment, storyId, isReply = false }) => (
    <div className={`border-l-2 border-gray-200 pl-4 ${isReply ? 'ml-6 mt-2' : 'mb-4'}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="font-medium text-sm">{comment.pseudonym}</span>
        <span className="text-xs text-muted-foreground">{formatTimeAgo(comment.created_at)}</span>
      </div>
      
      <p className="text-sm mb-3">{comment.content}</p>
      
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => toggleCommentReaction(comment.id, 'heart')}
            className="h-6 px-2 text-xs"
          >
            <Heart className="w-3 h-3 mr-1" />
            {comment.reaction_counts.heart}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => toggleCommentReaction(comment.id, 'hug')}
            className="h-6 px-2 text-xs"
          >
            🤗 {comment.reaction_counts.hug}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => toggleCommentReaction(comment.id, 'strength')}
            className="h-6 px-2 text-xs"
          >
            <Sparkles className="w-3 h-3 mr-1" />
            {comment.reaction_counts.strength}
          </Button>
        </div>
        
        {!isReply && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
            className="h-6 px-2 text-xs"
          >
            <Reply className="w-3 h-3 mr-1" />
            Reply
          </Button>
        )}
      </div>
      
      {replyingTo === comment.id && (
        <div className="mt-3 space-y-2">
          <Input
            placeholder="Your name (optional)"
            value={commentPseudonym}
            onChange={(e) => setCommentPseudonym(e.target.value)}
            className="text-sm"
          />
          <div className="flex gap-2">
            <Textarea
              placeholder="Write a supportive reply..."
              value={commentContent}
              onChange={(e) => setCommentContent(e.target.value)}
              className="text-sm min-h-[60px]"
            />
            <Button
              onClick={() => submitComment(storyId, comment.id)}
              disabled={!commentContent.trim()}
              size="sm"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
      
      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-3">
          {comment.replies.map(reply => (
            <CommentCard
              key={reply.id}
              comment={reply}
              storyId={storyId}
              isReply={true}
            />
          ))}
        </div>
      )}
    </div>
  )

  const NotificationBell = () => (
    <DropdownMenu open={showNotifications} onOpenChange={setShowNotifications}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <div className="p-3 border-b">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Notifications</h3>
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={markAllNotificationsRead}
                className="text-xs"
              >
                Mark all read
              </Button>
            )}
          </div>
        </div>
        
        <div className="max-h-96 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground text-sm">
              No notifications yet
            </div>
          ) : (
            notifications.map(notification => (
              <DropdownMenuItem
                key={notification.id}
                className={`p-3 cursor-pointer ${!notification.is_read ? 'bg-blue-50' : ''}`}
                onClick={() => {
                  if (!notification.is_read) {
                    markNotificationRead(notification.id)
                  }
                  setShowNotifications(false)
                }}
              >
                <div className="w-full">
                  <p className="text-sm">{notification.message}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatTimeAgo(notification.created_at)}
                  </p>
                </div>
              </DropdownMenuItem>
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading SupportGrove...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-4" />
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={fetchData}>Try Again</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Leaf className="h-6 w-6 text-primary" />
              <span className="text-xl font-bold text-foreground">SupportGrove</span>
              <span className="text-sm text-muted-foreground hidden sm:inline">Anonymous Support Community</span>
            </div>
            
            <nav className="flex items-center space-x-1">
              <Button 
                variant={currentView === 'home' ? 'default' : 'ghost'} 
                size="sm"
                onClick={() => setCurrentView('home')}
              >
                Home
              </Button>
              <Button 
                variant={currentView === 'browse' ? 'default' : 'ghost'} 
                size="sm"
                onClick={() => setCurrentView('browse')}
              >
                Browse
              </Button>
              <Button variant="ghost" size="sm">Resources</Button>
              <Button variant="ghost" size="sm">About</Button>
              <NotificationBell />
              <Button 
                onClick={() => setIsShareDialogOpen(true)}
                size="sm"
                className="bg-primary hover:bg-primary/90"
              >
                Share Story
              </Button>
            </nav>
          </div>
        </div>
      </header>

      <main>
        {currentView === 'home' && (
          <>
            {/* Hero Section */}
            <section className="hero-section">
              <div className="hero-content container-spacing section-spacing">
                <div className="text-center">
                  <div className="flex items-center justify-center space-x-3 mb-6">
                    <Leaf className="h-12 w-12 text-primary" />
                    <h1 className="hero-title">SupportGrove</h1>
                  </div>
                  <p className="unity-message">
                    We are not alone. Our truth connects us. Our stories are powerful and healing.
                  </p>
                  <div className="flex gap-6 justify-center mt-8">
                    <Button size="lg" onClick={() => setIsShareDialogOpen(true)} className="primary-button text-lg px-8 py-4">
                      Share Your Story
                    </Button>
                    <Button size="lg" variant="outline" onClick={() => setCurrentView('browse')} className="text-lg px-8 py-4 border-2 border-primary text-primary hover:bg-primary hover:text-white">
                      Browse Stories
                    </Button>
                  </div>
                </div>
              </div>
            </section>

            <div className="container-spacing">
            {/* Support Categories */}
            <section className="section-spacing">
              <h2 className="text-3xl font-bold mb-12 text-center">Support Categories</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {categories.map((category) => (
                  <Card key={category.id} className="support-card cursor-pointer"
                        onClick={() => {
                          setSelectedCategory(category.id)
                          setCurrentView('browse')
                        }}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: category.color }}
                        ></div>
                        <CardTitle className="text-lg">{category.name}</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="mb-3">
                        {category.description}
                      </CardDescription>
                      <p className="text-sm text-muted-foreground">
                        {category.story_count} stories shared
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            {/* Recent Stories */}
            <section className="section-spacing">
              <h2 className="text-3xl font-bold mb-12 text-center">Recent Stories</h2>
              <div className="space-y-8">
                {stories.slice(0, 3).map((story) => (
                  <Card key={story.id} className="story-card">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-xl mb-2">{story.title}</CardTitle>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                            <Badge variant="secondary" style={{ backgroundColor: story.category.color + '20', color: story.category.color }}>
                              {story.category.name}
                            </Badge>
                            <span>by {story.pseudonym}</span>
                            <span>•</span>
                            <span>{formatTimeAgo(story.created_at)}</span>
                          </div>
                          
                          {story.hashtags && story.hashtags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-3">
                              {story.hashtags.map((tag, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  <Hash className="w-3 h-3 mr-1" />
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    
                    <CardContent>
                      <p className="text-muted-foreground mb-4">No content available</p>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleStoryReaction(story.id, 'heart')}
                            className="text-muted-foreground hover:text-red-500"
                          >
                            <Heart className="w-4 h-4 mr-1" />
                            {story.heart_count}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleStoryReaction(story.id, 'hug')}
                            className="text-muted-foreground hover:text-orange-500"
                          >
                            🤗 {story.hug_count}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleStoryReaction(story.id, 'strength')}
                            className="text-muted-foreground hover:text-yellow-500"
                          >
                            <Sparkles className="w-4 h-4 mr-1" />
                            {story.strength_count}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleComments(story.id)}
                            className="text-muted-foreground hover:text-blue-500"
                          >
                            <MessageCircle className="w-4 h-4 mr-1" />
                            {comments[story.id]?.length || 0}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openForwardDialog(story)}
                            className="text-muted-foreground hover:text-green-500"
                          >
                            <Share className="w-4 h-4 mr-1" />
                            Forward
                          </Button>
                        </div>
                        <Button variant="outline" size="sm">Read More</Button>
                      </div>
                      
                      {/* Comments Section */}
                      <Collapsible open={expandedComments[story.id]}>
                        <CollapsibleContent className="mt-4 pt-4 border-t">
                          <div className="space-y-4">
                            {/* Comment Input */}
                            <div className="space-y-2">
                              <Input
                                placeholder="Your name (optional)"
                                value={commentPseudonym}
                                onChange={(e) => setCommentPseudonym(e.target.value)}
                                className="text-sm"
                              />
                              <div className="flex gap-2">
                                <Textarea
                                  placeholder="Share your thoughts or support..."
                                  value={commentContent}
                                  onChange={(e) => setCommentContent(e.target.value)}
                                  className="text-sm min-h-[80px]"
                                />
                                <Button
                                  onClick={() => submitComment(story.id)}
                                  disabled={!commentContent.trim()}
                                  size="sm"
                                >
                                  <Send className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>
                            
                            {/* Comments List */}
                            {comments[story.id] && comments[story.id].length > 0 ? (
                              <div className="space-y-4">
                                {comments[story.id].map(comment => (
                                  <CommentCard
                                    key={comment.id}
                                    comment={comment}
                                    storyId={story.id}
                                  />
                                ))}
                              </div>
                            ) : (
                              <p className="text-center text-muted-foreground text-sm py-4">
                                No comments yet. Be the first to share your thoughts.
                              </p>
                            )}
                          </div>
                        </CollapsibleContent>
                      </Collapsible>
                    </CardContent>
                  </Card>
                ))}
              </div>
              
              <div className="text-center mt-12">
                <Button variant="outline" onClick={() => setCurrentView('browse')} className="text-lg px-8 py-3">
                  View All Stories
                </Button>
              </div>
            </section>
            </div>
          </>
        )}

        {currentView === 'browse' && (
          <div className="container-spacing">
            {/* Search and Filter */}
            <div className="mb-8 space-y-4">
              <div className="flex gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    placeholder="Search stories or hashtags..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 form-input"
                  />
                </div>
                <Select value={selectedCategory?.toString() || ''} onValueChange={(value) => setSelectedCategory(value ? parseInt(value) : null)}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Categories</SelectItem>
                    {categories.map((category) => (
                      <SelectItem key={category.id} value={category.id.toString()}>
                        {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {(selectedCategory || searchQuery) && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Filters:</span>
                  {selectedCategory && (
                    <Badge variant="secondary" className="cursor-pointer" onClick={() => setSelectedCategory(null)}>
                      {categories.find(c => c.id === selectedCategory)?.name} ×
                    </Badge>
                  )}
                  {searchQuery && (
                    <Badge variant="secondary" className="cursor-pointer" onClick={() => setSearchQuery('')}>
                      "{searchQuery}" ×
                    </Badge>
                  )}
                </div>
              )}
            </div>

            {/* Stories Grid */}
            <div className="space-y-6">
              {filteredStories.map((story) => (
                <Card key={story.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-xl mb-2">{story.title}</CardTitle>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                          <Badge variant="secondary" style={{ backgroundColor: story.category.color + '20', color: story.category.color }}>
                            {story.category.name}
                          </Badge>
                          <span>by {story.pseudonym}</span>
                          <span>•</span>
                          <span>{formatTimeAgo(story.created_at)}</span>
                        </div>
                        
                        {story.hashtags && story.hashtags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-3">
                            {story.hashtags.map((tag, index) => (
                              <Badge key={index} variant="outline" className="text-xs cursor-pointer"
                                     onClick={() => setSearchQuery(tag)}>
                                <Hash className="w-3 h-3 mr-1" />
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    <p className="text-muted-foreground mb-4">No content available</p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleStoryReaction(story.id, 'heart')}
                          className="text-muted-foreground hover:text-red-500"
                        >
                          <Heart className="w-4 h-4 mr-1" />
                          {story.heart_count}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleStoryReaction(story.id, 'hug')}
                          className="text-muted-foreground hover:text-orange-500"
                        >
                          🤗 {story.hug_count}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleStoryReaction(story.id, 'strength')}
                          className="text-muted-foreground hover:text-yellow-500"
                        >
                          <Sparkles className="w-4 h-4 mr-1" />
                          {story.strength_count}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleComments(story.id)}
                          className="text-muted-foreground hover:text-blue-500"
                        >
                          <MessageCircle className="w-4 h-4 mr-1" />
                          {comments[story.id]?.length || 0}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openForwardDialog(story)}
                          className="text-muted-foreground hover:text-green-500"
                        >
                          <Share className="w-4 h-4 mr-1" />
                          Forward
                        </Button>
                      </div>
                      <Button variant="outline" size="sm">Read More</Button>
                    </div>
                    
                    {/* Comments Section */}
                    <Collapsible open={expandedComments[story.id]}>
                      <CollapsibleContent className="mt-4 pt-4 border-t">
                        <div className="space-y-4">
                          {/* Comment Input */}
                          <div className="space-y-2">
                            <Input
                              placeholder="Your name (optional)"
                              value={commentPseudonym}
                              onChange={(e) => setCommentPseudonym(e.target.value)}
                              className="text-sm"
                            />
                            <div className="flex gap-2">
                              <Textarea
                                placeholder="Share your thoughts or support..."
                                value={commentContent}
                                onChange={(e) => setCommentContent(e.target.value)}
                                className="text-sm min-h-[80px]"
                              />
                              <Button
                                onClick={() => submitComment(story.id)}
                                disabled={!commentContent.trim()}
                                size="sm"
                              >
                                <Send className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          
                          {/* Comments List */}
                          {comments[story.id] && comments[story.id].length > 0 ? (
                            <div className="space-y-4">
                              {comments[story.id].map(comment => (
                                <CommentCard
                                  key={comment.id}
                                  comment={comment}
                                  storyId={story.id}
                                />
                              ))}
                            </div>
                          ) : (
                            <p className="text-center text-muted-foreground text-sm py-4">
                              No comments yet. Be the first to share your thoughts.
                            </p>
                          )}
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            {filteredStories.length === 0 && (
              <div className="text-center py-12">
                <MessageCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">No stories found</h3>
                <p className="text-muted-foreground mb-4">
                  {searchQuery || selectedCategory 
                    ? "Try adjusting your search or filters" 
                    : "Be the first to share your story"}
                </p>
                <Button onClick={() => setIsShareDialogOpen(true)}>
                  Share Your Story
                </Button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Share Story Dialog */}
      <Dialog open={isShareDialogOpen} onOpenChange={setIsShareDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-primary">
              Share Your Story
            </DialogTitle>
            <DialogDescription>
              {shareStep === 1 
                ? "Your experience can help others on their healing journey. Share anonymously and safely."
                : "Help others by sharing what has supported your healing process."
              }
            </DialogDescription>
            {shareStep === 1 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
                <div className="flex items-start gap-2">
                  <Shield className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Privacy Reminder</p>
                    <p>Please avoid using real names (yours or others) when sharing your story. This helps protect everyone's privacy and maintains the safe, anonymous nature of our community.</p>
                  </div>
                </div>
              </div>
            )}
          </DialogHeader>

          {shareStep === 1 ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Title</label>
                <Input
                  placeholder="Give your story a meaningful title..."
                  value={shareForm.title}
                  onChange={(e) => setShareForm(prev => ({ ...prev, title: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <Select value={shareForm.category} onValueChange={(value) => setShareForm(prev => ({ ...prev, category: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((category) => (
                      <SelectItem key={category.id} value={category.id.toString()}>
                        {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Your Story</label>
                <Textarea
                  placeholder="Share your lived experience. Your story matters and can help others..."
                  value={shareForm.content}
                  onChange={(e) => setShareForm(prev => ({ ...prev, content: e.target.value }))}
                  className="min-h-[120px]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Hashtags (optional)</label>
                <Input
                  placeholder="recovery, hope, healing (separate with commas)"
                  value={shareForm.hashtags}
                  onChange={(e) => setShareForm(prev => ({ ...prev, hashtags: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Pseudonym (optional)</label>
                <Input
                  placeholder="Choose a name to use consistently (or leave blank for Anonymous)"
                  value={shareForm.pseudonym}
                  onChange={(e) => setShareForm(prev => ({ ...prev, pseudonym: e.target.value }))}
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setIsShareDialogOpen(false)}>
                  Close
                </Button>
                <Button onClick={handleShareSubmit}>
                  Continue to Guided Questions
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-primary">
                  What has helped you through the healing process?
                </label>
                <Textarea
                  placeholder="Share what strategies, people, activities, or insights have supported your healing journey..."
                  value={shareForm.healingProcess}
                  onChange={(e) => setShareForm(prev => ({ ...prev, healingProcess: e.target.value }))}
                  className="min-h-[100px]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-primary">
                  What is next in your life and recovery?
                </label>
                <Textarea
                  placeholder="Share your hopes, goals, or next steps in your recovery journey..."
                  value={shareForm.nextSteps}
                  onChange={(e) => setShareForm(prev => ({ ...prev, nextSteps: e.target.value }))}
                  className="min-h-[100px]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setShareStep(1)}>
                  Back
                </Button>
                <Button onClick={handleShareSubmit}>
                  Share Your Story
                </Button>
                <Button variant="outline" onClick={() => setIsShareDialogOpen(false)}>
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Forward Dialog */}
      <Dialog open={isForwardDialogOpen} onOpenChange={setIsForwardDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Forward This Conversation</DialogTitle>
            <DialogDescription>
              Share this story and its comments with friends or family members
            </DialogDescription>
          </DialogHeader>
          
          {forwardingStory && (
            <div className="space-y-6">
              {/* Story Preview */}
              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-medium mb-1">{forwardingStory.title}</h4>
                <p className="text-sm text-muted-foreground mb-2">
                  {forwardingStory.category.name} • {comments[forwardingStory.id]?.length || 0} comments
                </p>
                <div className="flex flex-wrap gap-1">
                  {forwardingStory.hashtags?.map(tag => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      #{tag}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Sharing Method Selection */}
              <div>
                <label className="text-sm font-medium mb-3 block">How would you like to share?</label>
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    variant={forwardMethod === 'link' ? 'default' : 'outline'}
                    onClick={() => setForwardMethod('link')}
                    className="flex items-center gap-2 h-auto p-4"
                  >
                    <Copy className="w-4 h-4" />
                    <div className="text-left">
                      <div className="font-medium">Copy Link</div>
                      <div className="text-xs opacity-70">Share via any platform</div>
                    </div>
                  </Button>
                  <Button
                    variant={forwardMethod === 'email' ? 'default' : 'outline'}
                    onClick={() => setForwardMethod('email')}
                    className="flex items-center gap-2 h-auto p-4"
                  >
                    <Mail className="w-4 h-4" />
                    <div className="text-left">
                      <div className="font-medium">Send Email</div>
                      <div className="text-xs opacity-70">Direct email delivery</div>
                    </div>
                  </Button>
                </div>
              </div>

              {/* Email Input (if email method selected) */}
              {forwardMethod === 'email' && (
                <div>
                  <label className="text-sm font-medium mb-2 block">Recipient Email</label>
                  <Input
                    type="email"
                    placeholder="friend@example.com"
                    value={forwardEmail}
                    onChange={(e) => setForwardEmail(e.target.value)}
                  />
                </div>
              )}

              {/* Personal Message */}
              <div>
                <label className="text-sm font-medium mb-2 block">Add a personal message (optional)</label>
                <Textarea
                  placeholder="I thought you might find this story helpful..."
                  value={forwardMessage}
                  onChange={(e) => setForwardMessage(e.target.value)}
                  rows={3}
                />
              </div>

              {/* Sender Name */}
              <div>
                <label className="text-sm font-medium mb-2 block">Your name (optional)</label>
                <Input
                  placeholder="Anonymous"
                  value={forwardSenderName}
                  onChange={(e) => setForwardSenderName(e.target.value)}
                />
              </div>

              {/* Share URL Display (if link method and URL generated) */}
              {forwardMethod === 'link' && shareUrl && (
                <div>
                  <label className="text-sm font-medium mb-2 block">Shareable Link</label>
                  <div className="flex gap-2">
                    <Input
                      value={shareUrl}
                      readOnly
                      className="font-mono text-xs"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(shareUrl)}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => setIsForwardDialogOpen(false)}
                  disabled={forwardLoading}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleForwardSubmit}
                  disabled={forwardLoading}
                >
                  {forwardLoading ? 'Processing...' : (
                    forwardMethod === 'email' ? 'Send Email' : 'Copy Link'
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Footer */}
      <footer className="border-t bg-muted/50 mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Leaf className="h-5 w-5 text-primary" />
              <span className="font-medium">SupportGrove.Online</span>
            </div>
            <div className="flex items-center space-x-6 text-sm text-muted-foreground">
              <span>Anonymous & Safe</span>
              <span>•</span>
              <span>Community Guidelines</span>
              <span>•</span>
              <span>Crisis Resources</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App

